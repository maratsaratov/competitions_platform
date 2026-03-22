import { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";
import s from "./Rating.module.css";

export default function Rating() {
  const { user } = useAuth();
  const [players, setPlayers] = useState([]);
  const [levels, setLevels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [gender, setGender] = useState("all");
  const [level, setLevel] = useState("all");
  const [importing, setImporting] = useState(false);
  const [importMsg, setImportMsg] = useState(null);
  const fileRef = useRef();

  useEffect(() => {
    api.get("/ratings/levels").then(r => setLevels(r.data));
  }, []);

  useEffect(() => {
    setLoading(true);
    const p = new URLSearchParams();
    if (search) p.append("q", search);
    if (gender !== "all") p.append("gender", gender);
    if (level !== "all") p.append("level", level);
    const t = setTimeout(() => {
      api.get(`/ratings?${p}`).then(r => { setPlayers(r.data); setLoading(false); });
    }, 300);
    return () => clearTimeout(t);
  }, [search, gender, level]);

  const handleImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true); setImportMsg(null);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await api.post("/ratings/import", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setImportMsg({ type:"success", text:`Импортировано ${r.data.imported} игроков` });
      api.get("/ratings").then(r2 => setPlayers(r2.data));
    } catch (err) {
      setImportMsg({ type:"error", text: err.response?.data?.error || "Ошибка импорта" });
    } finally { setImporting(false); e.target.value = ""; }
  };

  const medals = ["🥇","🥈","🥉"];

  return (
    <div className={s.root}>
      <div className={s.header}>
        <div>
          <h1 className={s.title}>Рейтинг</h1>
          <p className={s.sub}>Рейтинг игроков платформы</p>
        </div>
        {user?.is_superuser && (
          <div className={s.importWrap}>
            {importMsg && <span className={importMsg.type==="success"?s.importOk:s.importErr}>{importMsg.text}</span>}
            <input type="file" accept=".xlsx,.xls" ref={fileRef} style={{display:"none"}} onChange={handleImport}/>
            <button className={s.btnOutline} onClick={()=>fileRef.current.click()} disabled={importing}>
              {importing?"Импорт...":"↑ Импорт из Excel"}
            </button>
          </div>
        )}
      </div>

      <div className={s.controls}>
        <div className={s.searchWrap}>
          <span className={s.searchIcon}>🔍</span>
          <input className={s.search} placeholder="Поиск по имени..." value={search} onChange={e=>setSearch(e.target.value)}/>
          {search && <button className={s.clearBtn} onClick={()=>setSearch("")}>×</button>}
        </div>
        <div className={s.filterRow}>
          <div className={s.pills}>
            {[["all","Все"],["male","Мужчины"],["female","Женщины"]].map(([v,l])=>(
              <button key={v} className={`${s.pill} ${gender===v?s.pillActive:""}`} onClick={()=>setGender(v)}>{l}</button>
            ))}
          </div>
          {levels.length > 0 && (
            <div className={s.pills}>
              <button className={`${s.pill} ${level==="all"?s.pillActive:""}`} onClick={()=>setLevel("all")}>Все уровни</button>
              {levels.map(lv=>(
                <button key={lv} className={`${s.pill} ${level===lv?s.pillActive:""}`} onClick={()=>setLevel(lv)}>{lv}</button>
              ))}
            </div>
          )}
        </div>
      </div>

      {loading ? <div className={s.loaderWrap}><div className="loader"/></div> : players.length > 0 ? (
        <div className={s.tableWrap}>
          <table className={s.table}>
            <thead>
              <tr>
                <th className={s.thPlace}>#</th>
                <th>Игрок</th>
                <th>Город</th>
                <th>Уровень</th>
                <th className={s.thPoints}>Очки</th>
                <th>Турниры</th>
              </tr>
            </thead>
            <tbody>
              {players.map((p, i) => (
                <tr key={p.id} className={i < 3 ? s[`top${i+1}`] : ""}>
                  <td className={s.tdPlace}>
                    {i < 3 ? <span className={s.medal}>{medals[i]}</span> : <span className={s.placeNum}>{i+1}</span>}
                  </td>
                  <td>
                    <div className={s.playerName}>{p.full_name}</div>
                    <div className={s.playerGender}>{p.gender==="male"?"М":"Ж"}</div>
                  </td>
                  <td className={s.city}>{p.city||"—"}</td>
                  <td>{p.level ? <span className={s.levelBadge}>{p.level}</span> : "—"}</td>
                  <td className={s.tdPoints}><strong>{p.total_points}</strong></td>
                  <td className={s.tdTournaments}>{p.tournaments_played||0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className={s.empty}>
          <div className={s.emptyIcon}>📊</div>
          <h3>Игроки не найдены</h3>
          {search && <p>По запросу «{search}» ничего не найдено</p>}
        </div>
      )}
    </div>
  );
}
