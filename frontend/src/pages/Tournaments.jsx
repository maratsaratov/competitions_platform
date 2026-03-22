import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";
import s from "./Tournaments.module.css";

const TYPE_LABELS = { men_doubles:"Мужной парный", women_doubles:"Женский парный", mixed:"Микст", proam:"Про-Ам" };
const STATUS_LABELS = { upcoming:"Скоро", active:"Идёт", finished:"Завершён" };

export default function Tournaments() {
  const { user } = useAuth();
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("all");
  const [type, setType] = useState("all");

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (status !== "all") params.append("status", status);
    if (type !== "all") params.append("type", type);
    api.get(`/tournaments?${params}`).then(r => { setTournaments(r.data); setLoading(false); });
  }, [status, type]);

  return (
    <div className={s.root}>
      <div className={s.header}>
        <div>
          <h1 className={s.title}>Турниры</h1>
          <p className={s.sub}>Все соревнования платформы</p>
        </div>
        {user?.is_superuser && <Link to="/tournaments/add" className={s.btnPrimary}>+ Создать турнир</Link>}
      </div>

      <div className={s.filters}>
        <div className={s.filterRow}>
          <span className={s.filterLabel}>Статус:</span>
          <div className={s.pills}>
            {[["all","Все"],["upcoming","Предстоящие"],["active","Идут"],["finished","Завершены"]].map(([v,l]) => (
              <button key={v} className={`${s.pill} ${status===v?s.pillActive:""}`} onClick={()=>setStatus(v)}>{l}</button>
            ))}
          </div>
        </div>
        <div className={s.filterRow}>
          <span className={s.filterLabel}>Тип:</span>
          <div className={s.pills}>
            {[["all","Все"],["men_doubles","Мужной пар."],["women_doubles","Женский пар."],["mixed","Микст"],["proam","Про-Ам"]].map(([v,l]) => (
              <button key={v} className={`${s.pill} ${type===v?s.pillActive:""}`} onClick={()=>setType(v)}>{l}</button>
            ))}
          </div>
        </div>
      </div>

      {loading ? <div className={s.loader}><div className="loader"/></div> : (
        <div className={s.grid}>
          {tournaments.map(t => (
            <Link to={`/tournaments/${t.id}`} key={t.id} className={s.card}>
              <div className={s.cardTop}>
                <span className={`${s.typeBadge} ${s["type_"+t.category_type]}`}>{TYPE_LABELS[t.category_type]||t.category_type}</span>
                <span className={`${s.statusBadge} ${s["status_"+t.status]}`}>{STATUS_LABELS[t.status]}</span>
              </div>
              <div className={s.cardCategory}>{t.category}</div>
              <h3 className={s.cardTitle}>{t.title}</h3>
              {t.description && <p className={s.cardDesc}>{t.description.slice(0,110)}{t.description.length>110?"…":""}</p>}
              <div className={s.cardMeta}>
                {t.start_date && <span>📅 {new Date(t.start_date).toLocaleDateString("ru")}</span>}
                {t.end_date && <span>— {new Date(t.end_date).toLocaleDateString("ru")}</span>}
                {t.location && <span>📍 {t.location}</span>}
              </div>
              <div className={s.cardArrow}>→</div>
            </Link>
          ))}
          {tournaments.length===0 && (
            <div className={s.empty}>
              <div className={s.emptyIcon}>🏆</div>
              <h3>Турниров не найдено</h3>
              <p>Попробуйте изменить фильтры</p>
              {user?.is_superuser && <Link to="/tournaments/add" className={s.btnPrimary} style={{marginTop:"1rem"}}>Создать первый</Link>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
