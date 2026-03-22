import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import styles from "./Layout.module.css";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className={styles.root}>
      <nav className={styles.nav}>
        <NavLink to="/dashboard" className={styles.logo}>
          <span className={styles.logoIcon}>◈</span>
          <span className={styles.logoText}>PADEL<em>HUB</em></span>
        </NavLink>

        <div className={styles.links}>
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>
            Главная
          </NavLink>
          <NavLink to="/tournaments" className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>
            Турниры
          </NavLink>
          <NavLink to="/rating" className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>
            Рейтинг
          </NavLink>
          {user?.is_superuser && (
            <NavLink to="/admin/users" className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>
              Управление
            </NavLink>
          )}
        </div>

        <div className={styles.right}>
          {user?.is_superuser && <span className={styles.adminBadge}>ADMIN</span>}
          <NavLink to="/profile" className={styles.avatar}>
            {(user?.full_name || user?.email || "?")[0].toUpperCase()}
          </NavLink>
          <button className={styles.logoutBtn} onClick={handleLogout}>Выйти</button>
        </div>
      </nav>

      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
