import { useState, useEffect } from "react";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import s from "./AdminUsers.module.css";

export default function AdminUsers() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.get("/admin/users").then(r => { setUsers(r.data); setLoading(false); });
  };
  useEffect(load, []);

  const toggleSuper = async (uid) => {
    await api.post(`/admin/users/${uid}/toggle_super`);
    load();
  };

  return (
    <div className={s.root}>
      <div className={s.header}>
        <h1 className={s.title}>Управление пользователями</h1>
        <p className={s.sub}>Всего: {users.length}</p>
      </div>
      {loading ? <div style={{display:"flex",justifyContent:"center",padding:"3rem"}}><div className="loader"/></div> : (
        <div className={s.tableWrap}>
          <table className={s.table}>
            <thead><tr><th>#</th><th>Email</th><th>Имя</th><th>Роль</th><th>Дата регистрации</th><th>Действие</th></tr></thead>
            <tbody>
              {users.map((u, i) => (
                <tr key={u.id}>
                  <td className={s.tdNum}>{i+1}</td>
                  <td>{u.email}</td>
                  <td>{u.full_name || "—"}</td>
                  <td>{u.is_superuser ? <span className={s.adminBadge}>ADMIN</span> : <span className={s.userBadge}>Пользователь</span>}</td>
                  <td className={s.date}>{u.created_at ? new Date(u.created_at).toLocaleDateString("ru") : "—"}</td>
                  <td>
                    {u.id !== user?.id && (
                      <button className={u.is_superuser ? s.btnRevoke : s.btnGrant} onClick={() => toggleSuper(u.id)}>
                        {u.is_superuser ? "Снять admin" : "Сделать admin"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
