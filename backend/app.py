import os, json, math
import bcrypt
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from functools import wraps
from datetime import datetime, date
import pandas as pd

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True

CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost",
    "http://frontend:5173",
])

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:tennissuper369@localhost:5432/competitions_db")


def get_db():
    return psycopg2.connect(DATABASE_URL)


def q(sql, params=None, fetchone=False, fetchall=False, commit=False, returning=False):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            if commit:
                conn.commit()
                if returning:
                    return cur.fetchone()
                return cur.rowcount
            if fetchone:
                return cur.fetchone()
            if fetchall:
                return cur.fetchall()
    finally:
        conn.close()


def rows_to_list(rows):
    if not rows:
        return []
    result = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if isinstance(v, (datetime, date)):
                d[k] = v.isoformat()
        result.append(d)
    return result


def row_to_dict(row):
    if not row:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (datetime, date)):
            d[k] = v.isoformat()
    return d


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Необходима авторизация"}), 401
        return f(*args, **kwargs)
    return decorated


def superuser_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Необходима авторизация"}), 401
        if not session.get("is_superuser"):
            return jsonify({"error": "Недостаточно прав"}), 403
        return f(*args, **kwargs)
    return decorated


# ── AUTH ──────────────────────────────────────────────────────────────────────

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email и пароль обязательны"}), 400
    if len(password) < 6:
        return jsonify({"error": "Пароль минимум 6 символов"}), 400
    if q("SELECT id FROM users WHERE email=%s", (email,), fetchone=True):
        return jsonify({"error": "Пользователь с таким email уже существует"}), 409

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("INSERT INTO users (email, password_hash) VALUES (%s,%s) RETURNING id", (email, pw_hash))
            user_id = cur.fetchone()["id"]
            cur.execute("INSERT INTO profiles (user_id) VALUES (%s)", (user_id,))
            conn.commit()
        session["user_id"] = user_id
        session["email"] = email
        session["is_superuser"] = False
        return jsonify({"id": user_id, "email": email, "is_superuser": False}), 201
    finally:
        conn.close()


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = q("SELECT * FROM users WHERE email=%s", (email,), fetchone=True)
    if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        session["user_id"] = user["id"]
        session["email"] = user["email"]
        session["is_superuser"] = user["is_superuser"]
        return jsonify({"id": user["id"], "email": user["email"], "is_superuser": user["is_superuser"]})
    return jsonify({"error": "Неверный email или пароль"}), 401


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/auth/me")
def me():
    if "user_id" not in session:
        return jsonify(None), 200
    user = q("SELECT u.id, u.email, u.is_superuser, p.full_name, p.level, p.city FROM users u LEFT JOIN profiles p ON u.id=p.user_id WHERE u.id=%s",
             (session["user_id"],), fetchone=True)
    if not user:
        session.clear()
        return jsonify(None), 200
    return jsonify(dict(user))


# ── PROFILE ───────────────────────────────────────────────────────────────────

@app.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    p = q("SELECT * FROM profiles WHERE user_id=%s", (session["user_id"],), fetchone=True)
    return jsonify(row_to_dict(p))


@app.route("/api/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json()
    q("""UPDATE profiles SET full_name=%s, level=%s, birth_date=%s, phone=%s, city=%s, updated_at=NOW()
         WHERE user_id=%s""",
      (data.get("full_name"), data.get("level"), data.get("birth_date") or None,
       data.get("phone"), data.get("city"), session["user_id"]),
      commit=True)
    p = q("SELECT * FROM profiles WHERE user_id=%s", (session["user_id"],), fetchone=True)
    return jsonify(row_to_dict(p))


# ── TOURNAMENTS ───────────────────────────────────────────────────────────────

@app.route("/api/tournaments")
@login_required
def get_tournaments():
    status = request.args.get("status", "all")
    t_type = request.args.get("type", "all")
    sql = "SELECT t.*, u.email as creator_email FROM tournaments t LEFT JOIN users u ON t.created_by=u.id WHERE 1=1"
    params = []
    if status != "all":
        sql += " AND t.status=%s"; params.append(status)
    if t_type != "all":
        sql += " AND t.category_type=%s"; params.append(t_type)
    sql += " ORDER BY t.start_date DESC NULLS LAST"
    rows = q(sql, params or None, fetchall=True)
    return jsonify(rows_to_list(rows))


@app.route("/api/tournaments/<int:tid>")
@login_required
def get_tournament(tid):
    t = q("SELECT * FROM tournaments WHERE id=%s", (tid,), fetchone=True)
    if not t:
        return jsonify({"error": "Не найдено"}), 404
    d = row_to_dict(t)
    d["pairs"] = rows_to_list(q(
        "SELECT * FROM tournament_pairs WHERE tournament_id=%s ORDER BY group_number, id",
        (tid,), fetchall=True))
    d["group_matches"] = rows_to_list(q("""
        SELECT gm.*,
               p1.player1_name as p1_name, p1.player2_name as p1_name2,
               p2.player1_name as p2_name, p2.player2_name as p2_name2
        FROM group_matches gm
        LEFT JOIN tournament_pairs p1 ON gm.pair1_id=p1.id
        LEFT JOIN tournament_pairs p2 ON gm.pair2_id=p2.id
        WHERE gm.tournament_id=%s ORDER BY gm.group_number, gm.id
    """, (tid,), fetchall=True))
    d["bracket"] = rows_to_list(q("""
        SELECT bm.*,
               p1.player1_name as p1_name, p1.player2_name as p1_name2,
               p2.player1_name as p2_name, p2.player2_name as p2_name2
        FROM bracket_matches bm
        LEFT JOIN tournament_pairs p1 ON bm.pair1_id=p1.id
        LEFT JOIN tournament_pairs p2 ON bm.pair2_id=p2.id
        WHERE bm.tournament_id=%s ORDER BY bm.round DESC, bm.match_number
    """, (tid,), fetchall=True))
    return jsonify(d)


@app.route("/api/tournaments", methods=["POST"])
@superuser_required
def create_tournament():
    data = request.get_json()
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Название обязательно"}), 400

    # group_format now comes fully from frontend (num_groups + pairs_per_group editable)
    num_groups = int(data.get("num_groups", 2))
    pairs_per_group = int(data.get("pairs_per_group", 4))
    total_pairs = num_groups * pairs_per_group
    group_format = json.dumps({
        "total_pairs": total_pairs,
        "groups": num_groups,
        "pairs_per_group": pairs_per_group
    })

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""INSERT INTO tournaments
                (title,category,category_type,description,start_date,end_date,location,group_format,bracket_size,created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (title, data.get("category",""), data.get("category_type",""),
                 data.get("description",""), data.get("start_date") or None,
                 data.get("end_date") or None, data.get("location",""),
                 group_format, int(data.get("bracket_size", 8)), session["user_id"]))
            tid = cur.fetchone()["id"]
            conn.commit()
        return jsonify({"id": tid}), 201
    finally:
        conn.close()


@app.route("/api/tournaments/<int:tid>/format", methods=["PUT"])
@superuser_required
def update_tournament_format(tid):
    """Update group format after creation (e.g. actual registrations differ)"""
    data = request.get_json()
    num_groups = int(data.get("num_groups", 2))
    pairs_per_group = int(data.get("pairs_per_group", 4))
    total_pairs = num_groups * pairs_per_group
    group_format = json.dumps({
        "total_pairs": total_pairs,
        "groups": num_groups,
        "pairs_per_group": pairs_per_group
    })
    q("UPDATE tournaments SET group_format=%s, bracket_size=%s WHERE id=%s",
      (group_format, int(data.get("bracket_size", 8)), tid), commit=True)
    return jsonify({"ok": True})


@app.route("/api/tournaments/<int:tid>/status", methods=["PUT"])
@superuser_required
def update_tournament_status(tid):
    data = request.get_json()
    status = data.get("status")
    if status not in ("upcoming", "active", "finished"):
        return jsonify({"error": "Неверный статус"}), 400
    q("UPDATE tournaments SET status=%s WHERE id=%s", (status, tid), commit=True)
    return jsonify({"ok": True})


@app.route("/api/tournaments/<int:tid>/pairs", methods=["POST"])
@superuser_required
def add_pair(tid):
    data = request.get_json()
    player1 = (data.get("player1_name") or "").strip()
    if not player1:
        return jsonify({"error": "Имя первого игрока обязательно"}), 400
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""INSERT INTO tournament_pairs (tournament_id, player1_name, player2_name, group_number)
                           VALUES (%s,%s,%s,%s) RETURNING id""",
                        (tid, player1, data.get("player2_name","") or None,
                         data.get("group_number") or None))
            pid = cur.fetchone()["id"]
            conn.commit()
        return jsonify({"id": pid}), 201
    finally:
        conn.close()


@app.route("/api/tournaments/<int:tid>/pairs/<int:pid>", methods=["DELETE"])
@superuser_required
def delete_pair(tid, pid):
    q("DELETE FROM tournament_pairs WHERE id=%s AND tournament_id=%s", (pid, tid), commit=True)
    return jsonify({"ok": True})


# ── GROUP MATCHES ─────────────────────────────────────────────────────────────

@app.route("/api/tournaments/<int:tid>/group_matches/generate", methods=["POST"])
@superuser_required
def generate_group_matches(tid):
    """Generate round-robin matches for all groups"""
    pairs = q("SELECT * FROM tournament_pairs WHERE tournament_id=%s AND group_number IS NOT NULL ORDER BY group_number, id",
              (tid,), fetchall=True)
    if not pairs:
        return jsonify({"error": "Нет участников с назначенными группами"}), 400

    # Group pairs by group_number
    groups = {}
    for p in pairs:
        g = p["group_number"]
        if g not in groups:
            groups[g] = []
        groups[g].append(p)

    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Clear existing group matches
            cur.execute("DELETE FROM group_matches WHERE tournament_id=%s", (tid,))
            count = 0
            for g_num, g_pairs in groups.items():
                # Round-robin: every pair plays every other pair
                for i in range(len(g_pairs)):
                    for j in range(i + 1, len(g_pairs)):
                        cur.execute("""INSERT INTO group_matches
                            (tournament_id, group_number, pair1_id, pair2_id)
                            VALUES (%s,%s,%s,%s)""",
                            (tid, g_num, g_pairs[i]["id"], g_pairs[j]["id"]))
                        count += 1
            conn.commit()
        return jsonify({"generated": count})
    finally:
        conn.close()


@app.route("/api/tournaments/<int:tid>/group_matches/<int:mid>/score", methods=["PUT"])
@superuser_required
def set_group_match_score(tid, mid):
    """Set score for a group match and determine winner"""
    data = request.get_json()
    score1 = (data.get("score_pair1") or "").strip()
    score2 = (data.get("score_pair2") or "").strip()

    match = q("SELECT * FROM group_matches WHERE id=%s AND tournament_id=%s", (mid, tid), fetchone=True)
    if not match:
        return jsonify({"error": "Матч не найден"}), 404

    # Determine winner: parse scores like "6:3 6:4" — count sets won
    winner_id = None
    if score1 and score2:
        winner_id = _determine_winner(match["pair1_id"], match["pair2_id"], score1, score2)

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""UPDATE group_matches
                SET score_pair1=%s, score_pair2=%s, winner_pair_id=%s, played_at=NOW()
                WHERE id=%s""",
                (score1, score2, winner_id, mid))
            conn.commit()
        return jsonify({"ok": True, "winner_pair_id": winner_id})
    finally:
        conn.close()


def _determine_winner(pair1_id, pair2_id, score1_str, score2_str):
    """Parse scores like '6:3 6:4' and return winning pair id"""
    try:
        sets1 = score1_str.strip().split()
        sets2 = score2_str.strip().split()
        wins1, wins2 = 0, 0
        for s in sets1:
            parts = s.replace("-", ":").split(":")
            if len(parts) == 2 and int(parts[0]) > int(parts[1]):
                wins1 += 1
        for s in sets2:
            parts = s.replace("-", ":").split(":")
            if len(parts) == 2 and int(parts[0]) > int(parts[1]):
                wins2 += 1
        if wins1 > wins2:
            return pair1_id
        elif wins2 > wins1:
            return pair2_id
    except Exception:
        pass
    return None


# ── BRACKET GENERATION ────────────────────────────────────────────────────────

@app.route("/api/tournaments/<int:tid>/bracket/generate", methods=["POST"])
@superuser_required
def generate_bracket(tid):
    """Generate playoff bracket from group stage results.
    Top N pairs from each group advance (N = bracket_size / num_groups).
    """
    t = q("SELECT * FROM tournaments WHERE id=%s", (tid,), fetchone=True)
    if not t:
        return jsonify({"error": "Турнир не найден"}), 404

    bracket_size = t["bracket_size"]
    gf = t["group_format"] or {}
    num_groups = gf.get("groups", 2)

    # Build group standings from match results
    pairs = q("SELECT * FROM tournament_pairs WHERE tournament_id=%s AND group_number IS NOT NULL",
              (tid,), fetchall=True)
    matches = q("SELECT * FROM group_matches WHERE tournament_id=%s", (tid,), fetchall=True)

    # Calculate wins/losses per pair
    stats = {}  # pair_id -> {wins, losses, points_for, points_against}
    for p in (pairs or []):
        stats[p["id"]] = {"pair": p, "wins": 0, "losses": 0}

    for m in (matches or []):
        if not m["winner_pair_id"]:
            continue
        loser_id = m["pair2_id"] if m["winner_pair_id"] == m["pair1_id"] else m["pair1_id"]
        if m["winner_pair_id"] in stats:
            stats[m["winner_pair_id"]]["wins"] += 1
        if loser_id in stats:
            stats[loser_id]["losses"] += 1

    # Group standings: sort by wins desc
    groups = {}
    for pid, s in stats.items():
        g = s["pair"]["group_number"]
        if g not in groups:
            groups[g] = []
        groups[g].append(s)

    for g in groups:
        groups[g].sort(key=lambda x: x["wins"], reverse=True)

    # How many advance per group
    advance_per_group = max(1, bracket_size // num_groups)

    # Collect advancers: top N from each group
    advancers = []
    for g_num in sorted(groups.keys()):
        advancers.extend(groups[g_num][:advance_per_group])

    # Pad to bracket_size if needed
    while len(advancers) < bracket_size:
        advancers.append(None)
    advancers = advancers[:bracket_size]

    # Build bracket rounds
    # Round 1 = first round (e.g. quarterfinals for bracket_size=8)
    # Round log2(bracket_size) = first round matches
    # Round 1 = Final
    num_rounds = int(math.log2(bracket_size)) if bracket_size > 1 else 1
    first_round = num_rounds  # highest number = earliest round

    # Seed the bracket: 1v(last), 2v(second last), etc.
    # Seeds: [1,2,3,...,n] -> match 1: seed1 vs seed(n), match2: seed2 vs seed(n-1)
    seeds = advancers  # already ordered by group performance

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bracket_matches WHERE tournament_id=%s", (tid,))

            match_count = bracket_size // 2
            for i in range(match_count):
                pair1 = seeds[i]
                pair2 = seeds[bracket_size - 1 - i]
                p1_id = pair1["pair"]["id"] if pair1 else None
                p2_id = pair2["pair"]["id"] if pair2 else None
                cur.execute("""INSERT INTO bracket_matches
                    (tournament_id, round, match_number, pair1_id, pair2_id)
                    VALUES (%s,%s,%s,%s,%s)""",
                    (tid, first_round, i + 1, p1_id, p2_id))

            # Create empty slots for subsequent rounds
            for rnd in range(first_round - 1, 0, -1):
                rnd_matches = 2 ** (rnd - 1)
                for mn in range(1, rnd_matches + 1):
                    cur.execute("""INSERT INTO bracket_matches
                        (tournament_id, round, match_number)
                        VALUES (%s,%s,%s)""",
                        (tid, rnd, mn))

            conn.commit()
        return jsonify({"ok": True, "advancers": len([a for a in advancers if a])})
    finally:
        conn.close()


@app.route("/api/tournaments/<int:tid>/bracket/<int:mid>/score", methods=["PUT"])
@superuser_required
def set_bracket_score(tid, mid):
    """Set score for a bracket match and propagate winner to next round"""
    data = request.get_json()
    score1 = (data.get("score_pair1") or "").strip()
    score2 = (data.get("score_pair2") or "").strip()

    match = q("SELECT * FROM bracket_matches WHERE id=%s AND tournament_id=%s", (mid, tid), fetchone=True)
    if not match:
        return jsonify({"error": "Матч не найден"}), 404

    winner_id = None
    if score1 and score2:
        winner_id = _determine_winner(match["pair1_id"], match["pair2_id"], score1, score2)

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""UPDATE bracket_matches
                SET score_pair1=%s, score_pair2=%s, winner_pair_id=%s
                WHERE id=%s""",
                (score1, score2, winner_id, mid))

            # Propagate winner to next round
            if winner_id and match["round"] > 1:
                next_round = match["round"] - 1
                next_match_num = math.ceil(match["match_number"] / 2)
                next_match = q("""SELECT * FROM bracket_matches
                    WHERE tournament_id=%s AND round=%s AND match_number=%s""",
                    (tid, next_round, next_match_num), fetchone=True)
                if next_match:
                    # odd match_number -> pair1 slot, even -> pair2 slot
                    if match["match_number"] % 2 == 1:
                        cur.execute("UPDATE bracket_matches SET pair1_id=%s WHERE id=%s",
                                    (winner_id, next_match["id"]))
                    else:
                        cur.execute("UPDATE bracket_matches SET pair2_id=%s WHERE id=%s",
                                    (winner_id, next_match["id"]))

            conn.commit()
        return jsonify({"ok": True, "winner_pair_id": winner_id})
    finally:
        conn.close()


# ── RATING ────────────────────────────────────────────────────────────────────

@app.route("/api/ratings")
@login_required
def get_ratings():
    search = request.args.get("q", "").strip()
    gender = request.args.get("gender", "all")
    level = request.args.get("level", "all")
    sql = "SELECT * FROM ratings WHERE 1=1"
    params = []
    if search:
        sql += " AND full_name ILIKE %s"; params.append(f"%{search}%")
    if gender != "all":
        sql += " AND gender=%s"; params.append(gender)
    if level != "all":
        sql += " AND level=%s"; params.append(level)
    sql += " ORDER BY total_points DESC"
    rows = q(sql, params or None, fetchall=True)
    result = []
    for i, r in enumerate(rows or []):
        d = row_to_dict(r)
        d["rank"] = i + 1
        result.append(d)
    return jsonify(result)


@app.route("/api/ratings/levels")
@login_required
def get_levels():
    rows = q("SELECT DISTINCT level FROM ratings WHERE level IS NOT NULL ORDER BY level", fetchall=True)
    return jsonify([r["level"] for r in (rows or [])])


@app.route("/api/ratings/import", methods=["POST"])
@superuser_required
def import_ratings():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Файл не выбран"}), 400
    os.makedirs("uploads", exist_ok=True)
    path = os.path.join("uploads", f.filename)
    f.save(path)
    try:
        df = pd.read_excel(path)
        col_map = {}
        for col in df.columns:
            lc = str(col).lower()
            if any(x in lc for x in ["фио","имя","name"]): col_map["full_name"] = col
            elif any(x in lc for x in ["место","place","rank"]): col_map["place"] = col
            elif any(x in lc for x in ["город","city"]): col_map["city"] = col
            elif any(x in lc for x in ["уровень","level"]): col_map["level"] = col
            elif any(x in lc for x in ["очк","балл","point"]): col_map["total_points"] = col
            elif any(x in lc for x in ["турнир","tournament"]): col_map["tournaments_played"] = col
            elif any(x in lc for x in ["пол","gender","sex"]): col_map["gender"] = col

        conn = get_db()
        inserted = 0
        with conn.cursor() as cur:
            cur.execute("TRUNCATE ratings RESTART IDENTITY")
            for i, row in df.iterrows():
                full_name = str(row.get(col_map.get("full_name",""), "")).strip()
                if not full_name or full_name == "nan":
                    continue
                place = row.get(col_map.get("place",""), i+1)
                city = str(row.get(col_map.get("city",""), "")).strip()
                level = str(row.get(col_map.get("level",""), "")).strip()
                total_points = int(row.get(col_map.get("total_points",""), 0) or 0)
                played = int(row.get(col_map.get("tournaments_played",""), 0) or 0)
                gender_raw = str(row.get(col_map.get("gender",""), "")).strip().lower()
                gender_val = "female" if gender_raw in ("ж","f","female","жен") else "male"
                cur.execute("""INSERT INTO ratings (place,full_name,city,level,total_points,tournaments_played,gender)
                               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                            (place, full_name, city if city != "nan" else None,
                             level if level != "nan" else None, total_points, played, gender_val))
                inserted += 1
            conn.commit()
        conn.close()
        return jsonify({"imported": inserted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── ADMIN ─────────────────────────────────────────────────────────────────────

@app.route("/api/admin/users")
@superuser_required
def admin_users():
    rows = q("SELECT u.id, u.email, u.is_superuser, u.created_at, p.full_name FROM users u LEFT JOIN profiles p ON u.id=p.user_id ORDER BY u.id", fetchall=True)
    return jsonify(rows_to_list(rows))


@app.route("/api/admin/users/<int:uid>/toggle_super", methods=["POST"])
@superuser_required
def toggle_superuser(uid):
    if uid == session["user_id"]:
        return jsonify({"error": "Нельзя изменить свои права"}), 400
    q("UPDATE users SET is_superuser = NOT is_superuser WHERE id=%s", (uid,), commit=True)
    return jsonify({"ok": True})


@app.route("/api/stats")
@login_required
def stats():
    total = q("SELECT COUNT(*) as c FROM tournaments", fetchone=True)["c"]
    upcoming = q("SELECT COUNT(*) as c FROM tournaments WHERE status='upcoming'", fetchone=True)["c"]
    active = q("SELECT COUNT(*) as c FROM tournaments WHERE status='active'", fetchone=True)["c"]
    players = q("SELECT COUNT(*) as c FROM ratings", fetchone=True)["c"]
    return jsonify({"total_tournaments": total, "upcoming": upcoming, "active": active, "players": players})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
