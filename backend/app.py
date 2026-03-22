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


def serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def rows_to_list(rows):
    if not rows:
        return []
    return [dict(r) for r in rows]


def row_to_dict(row):
    if not row:
        return None
    return dict(row)


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
    result = []
    for r in (rows or []):
        d = dict(r)
        for k, v in d.items():
            if isinstance(v, (datetime, date)):
                d[k] = v.isoformat()
        result.append(d)
    return jsonify(result)


@app.route("/api/tournaments/<int:tid>")
@login_required
def get_tournament(tid):
    t = q("SELECT * FROM tournaments WHERE id=%s", (tid,), fetchone=True)
    if not t:
        return jsonify({"error": "Не найдено"}), 404
    d = dict(t)
    for k, v in d.items():
        if isinstance(v, (datetime, date)):
            d[k] = v.isoformat()

    pairs = rows_to_list(q("SELECT * FROM tournament_pairs WHERE tournament_id=%s ORDER BY group_number, id", (tid,), fetchall=True))
    group_matches = rows_to_list(q("""
        SELECT gm.*, p1.player1_name as p1_name, p1.player2_name as p1_name2,
               p2.player1_name as p2_name, p2.player2_name as p2_name2
        FROM group_matches gm
        LEFT JOIN tournament_pairs p1 ON gm.pair1_id=p1.id
        LEFT JOIN tournament_pairs p2 ON gm.pair2_id=p2.id
        WHERE gm.tournament_id=%s ORDER BY gm.group_number
    """, (tid,), fetchall=True))
    bracket = rows_to_list(q("""
        SELECT bm.*, p1.player1_name as p1_name, p1.player2_name as p1_name2,
               p2.player1_name as p2_name, p2.player2_name as p2_name2
        FROM bracket_matches bm
        LEFT JOIN tournament_pairs p1 ON bm.pair1_id=p1.id
        LEFT JOIN tournament_pairs p2 ON bm.pair2_id=p2.id
        WHERE bm.tournament_id=%s ORDER BY bm.round DESC, bm.match_number
    """, (tid,), fetchall=True))

    for m in group_matches:
        for k, v in m.items():
            if isinstance(v, (datetime, date)):
                m[k] = v.isoformat()

    d["pairs"] = pairs
    d["group_matches"] = group_matches
    d["bracket"] = bracket
    return jsonify(d)


@app.route("/api/tournaments", methods=["POST"])
@superuser_required
def create_tournament():
    data = request.get_json()
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Название обязательно"}), 400

    total_pairs = int(data.get("total_pairs", 8))
    groups = max(2, math.ceil(total_pairs / 4))
    pairs_per_group = math.ceil(total_pairs / groups)
    group_format = json.dumps({"total_pairs": total_pairs, "groups": groups, "pairs_per_group": pairs_per_group})

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""INSERT INTO tournaments
                (title,category,category_type,description,start_date,end_date,location,group_format,bracket_size,created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (title, data.get("category",""), data.get("category_type",""),
                 data.get("description",""), data.get("start_date") or None,
                 data.get("end_date") or None, data.get("location",""),
                 group_format, int(data.get("bracket_size",8)), session["user_id"]))
            tid = cur.fetchone()["id"]
            conn.commit()
        return jsonify({"id": tid}), 201
    finally:
        conn.close()


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
                        (tid, player1, data.get("player2_name","") or None, data.get("group_number") or None))
            pid = cur.fetchone()["id"]
            conn.commit()
        return jsonify({"id": pid}), 201
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
        d = dict(r)
        d["rank"] = i + 1
        for k, v in d.items():
            if isinstance(v, (datetime, date)):
                d[k] = v.isoformat()
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
            if any(x in lc for x in ["фио","имя","name"]):
                col_map["full_name"] = col
            elif any(x in lc for x in ["место","place","rank"]):
                col_map["place"] = col
            elif any(x in lc for x in ["город","city"]):
                col_map["city"] = col
            elif any(x in lc for x in ["уровень","level"]):
                col_map["level"] = col
            elif any(x in lc for x in ["очк","балл","point"]):
                col_map["total_points"] = col
            elif any(x in lc for x in ["турнир","tournament"]):
                col_map["tournaments_played"] = col
            elif any(x in lc for x in ["пол","gender","sex"]):
                col_map["gender"] = col

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
    result = []
    for r in (rows or []):
        d = dict(r)
        for k, v in d.items():
            if isinstance(v, (datetime, date)):
                d[k] = v.isoformat()
        result.append(d)
    return jsonify(result)


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
