import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";
import s from "./Dashboard.module.css";

const TYPE_LABELS = { men_doubles:"Мужной парный", women_doubles:"Женский парный", mixed:"Микст", proam:"Про-Ам" };
const STATUS_LABELS = { upcoming:"Скоро", active:"Идёт", finished:"Завершён" };

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    api.get("/stats").then(r => setStats(r.data));
    api.get("/tournaments").then(r => setRecent(r.data.slice(0, 3)));
  }, []);

  return (
    <div className={s.root}>
      <div className={s.header}>
        <div>
          <h1 className={s.title}>Привет, {user?.full_name || user?.email}!</h1>
          <p className={s.sub}>{user?.is_superuser ? "Администратор платформы" : "Участник турниров"}</p>
        </div>
        {user?.is_superuser && <Link to="/tournaments/add" className={s.btnPrimary}>+ Создать турнир</Link>}
      </div>

      <div className={s.statsRow}>
        {[
          ["Всего турниров", stats?.total_tournaments ?? "—", false],
          ["Предстоящих", stats?.upcoming ?? "—", true],
          ["Активных", stats?.active ?? "—", false],
          ["Игроков в рейтинге", stats?.players ?? "—", false],
        ].map(([label, val, accent]) => (
          <div key={label} className={`${s.statCard} ${accent ? s.statAccent : ""}`}>
            <span className={s.statNum}>{val}</span>
            <span className={s.statLabel}>{label}</span>
          </div>
        ))}
      </div>

      <section>
        <div className={s.sectionHead}>
          <h2 className={s.sectionTitle}>Последние турниры</h2>
          <Link to="/tournaments" className={s.sectionLink}>Все турниры →</Link>
        </div>
        <div className={s.grid}>
          {recent.map(t => (
            <Link to={`/tournaments/${t.id}`} key={t.id} className={s.card}>
              <div className={s.cardTop}>
                <span className={`${s.typeBadge} ${s["type_" + t.category_type]}`}>{TYPE_LABELS[t.category_type] || t.category_type}</span>
                <span className={`${s.statusBadge} ${s["status_" + t.status]}`}>{STATUS_LABELS[t.status]}</span>
              </div>
              <div className={s.cardCategory}>{t.category}</div>
              <h3 className={s.cardTitle}>{t.title}</h3>
              <div className={s.cardMeta}>
                {t.start_date && <span>📅 {new Date(t.start_date).toLocaleDateString("ru")}</span>}
                {t.location && <span>📍 {t.location}</span>}
              </div>
            </Link>
          ))}
          {recent.length === 0 && (
            <div className={s.empty}>
              <div>🏆</div>
              <p>Турниров пока нет{user?.is_superuser && <> · <Link to="/tournaments/add">Создайте первый</Link></>}</p>
            </div>
          )}
        </div>
      </section>

      {!user?.full_name && (
        <div className={s.nudge}>
          <span className={s.nudgeIcon}>👤</span>
          <div>
            <strong>Заполните профиль</strong>
            <p>Добавьте ФИО, уровень и дату рождения для участия в турнирах</p>
          </div>
          <Link to="/profile" className={s.btnOutline}>Заполнить</Link>
        </div>
      )}
    </div>
  );
}
