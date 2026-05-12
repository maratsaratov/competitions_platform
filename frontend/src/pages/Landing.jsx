import { Link } from "react-router-dom";
import s from "./Landing.module.css";

export default function Landing() {
  return (
    <div className={s.root}>
      <nav className={s.nav}>
        <div className={s.logo}>
          <span className={s.logoIcon}>◈</span>
          <span className={s.logoText}>PADEL<em>HUB</em></span>
        </div>
        <div className={s.navRight}>
          <Link to="/login" className={s.btnGhost}>Войти</Link>
          <Link to="/register" className={s.btnPrimary}>Регистрация</Link>
        </div>
      </nav>

      <section className={s.hero}>
        <div className={s.heroBg}>
          <div className={s.grid}/>
          <div className={s.glow}/>
        </div>
        <div className={s.heroContent}>
          <div className={s.heroTag}>◈ Падел-теннис · Россия</div>
          <h1 className={s.heroTitle}>
            <span>ТВОЙ</span>
            <span className={s.accent}>ТУРНИР</span>
            <span>ЗДЕСЬ</span>
          </h1>
          <p className={s.heroSub}>Регистрируйся, участвуй в турнирах, следи за рейтингом. Платформа для организации соревнований по падел-теннису.</p>
          <div className={s.heroCta}>
            <Link to="/register" className={s.ctaPrimary}>Начать бесплатно</Link>
            <Link to="/login" className={s.ctaSecondary}>Уже есть аккаунт →</Link>
          </div>
        </div>
        <div className={s.heroStats}>
          {[["100+","Игроков"],["24","Турнира"],["5","Городов"]].map(([n,l])=>(
            <div key={l} className={s.statItem}>
              <span className={s.statNum}>{n}</span>
              <span className={s.statLabel}>{l}</span>
            </div>
          ))}
        </div>
      </section>

      <section className={s.features}>
        <div className={s.featuresGrid}>
          {[
            ["⚡","Быстрая регистрация","Создай аккаунт за минуту и сразу участвуй в турнирах своего уровня"],
            ["🏆","Турнирные сетки","Групповой этап и плей-офф с автоматическим расчётом групп"],
            ["📊","Живой рейтинг","Актуальный рейтинг всех игроков с фильтрами по уровню и городу"],
            ["👥","Все форматы","Мужной парный, женский парный, микст, про-ам — выбирай формат"],
          ].map(([icon,title,desc])=>(
            <div key={title} className={s.featureCard}>
              <div className={s.featureIcon}>{icon}</div>
              <h3>{title}</h3>
              <p>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className={s.footer}>
        <span>© 2025 PadelHub</span>
        <span>Платформа для организации соревнований по падел-теннису</span>
      </footer>
    </div>
  );
}
