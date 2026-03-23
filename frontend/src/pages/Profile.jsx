import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";
import s from "./Profile.module.css";

const LEVELS = ["2.0","2.5","3.0","3.5","4.0","4.5","5.0","5.5","6.0","6.5","7.0"];

export default function Profile() {
  const { user } = useAuth();
  const [form, setForm] = useState({ full_name:"", level:"", birth_date:"", phone:"", city:"" });
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/profile").then(r => {
      if (r.data) setForm({
        full_name: r.data.full_name || "",
        level: r.data.level || "",
        birth_date: r.data.birth_date ? r.data.birth_date.slice(0,10) : "",
        phone: r.data.phone || "",
        city: r.data.city || "",
      });
    });
  }, []);

  const submit = async (e) => {
    e.preventDefault(); setMsg(null); setLoading(true);
    try {
      await api.put("/profile", form);
      setMsg({ type:"success", text:"Профиль обновлён" });
    } catch { setMsg({ type:"error", text:"Ошибка сохранения" }); }
    finally { setLoading(false); }
  };

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  return (
    <div className={s.root}>
      <div className={s.header}>
        <h1 className={s.title}>Личный кабинет</h1>
        <p className={s.sub}>{user?.email}</p>
      </div>
      <div className={s.layout}>
        <div className={s.avatarCard}>
          <div className={s.avatarBig}>{(user?.email || "?")[0].toUpperCase()}</div>
          <div>
            <div className={s.avatarName}>{form.full_name || "Имя не указано"}</div>
            <div className={s.avatarEmail}>{user?.email}</div>
            {form.level && <span className={s.levelBadge}>Уровень {form.level}</span>}
            {user?.is_superuser && <span className={s.adminBadge}>ADMIN</span>}
          </div>
        </div>
        <div className={s.formCard}>
          <h3 className={s.formTitle}>Редактировать данные</h3>
          {msg && <div className={msg.type === "success" ? s.success : s.error}>{msg.text}</div>}
          <form onSubmit={submit}>
            <div className={s.row}>
              <div className={s.group}><label>ФИО</label><input type="text" value={form.full_name} onChange={set("full_name")} placeholder="Иванов Иван Иванович"/></div>
              <div className={s.group}><label>Город</label><input type="text" value={form.city} onChange={set("city")} placeholder="Москва"/></div>
            </div>
            <div className={s.row}>
              <div className={s.group}>
                <label>Уровень игры</label>
                <select value={form.level} onChange={set("level")}>
                  <option value="">Не указан</option>
                  {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
              <div className={s.group}><label>Дата рождения</label><input type="date" value={form.birth_date} onChange={set("birth_date")}/></div>
            </div>
            <div className={s.group}><label>Телефон</label><input type="tel" value={form.phone} onChange={set("phone")} placeholder="+7 999 123-45-67"/></div>
            <div className={s.actions}>
              <button type="submit" className={s.submit} disabled={loading}>{loading?"Сохранение...":"Сохранить изменения"}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
