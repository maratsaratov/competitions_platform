import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import s from "./Auth.module.css";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) { setError("Пароли не совпадают"); return; }
    if (form.password.length < 6) { setError("Пароль минимум 6 символов"); return; }
    setLoading(true);
    try {
      await register(form.email, form.password);
      navigate("/profile");
    } catch (err) {
      setError(err.response?.data?.error || "Ошибка регистрации");
    } finally { setLoading(false); }
  };

  return (
    <div className={s.split}>
      <div className={s.visual}>
        <Link to="/" className={s.logo}><span className={s.logoIcon}>◈</span><span className={s.logoText}>PADEL<em>HUB</em></span></Link>
        <div className={s.visualText}><h2>Присоединись<br/>к игре</h2><p>Регистрируйся и участвуй в лучших турнирах по падел-теннису</p></div>
        <div className={s.decoCircle1}/><div className={s.decoCircle2}/><div className={s.decoNet}/>
      </div>
      <div className={s.formSide}>
        <div className={s.formWrap}>
          <h1 className={s.title}>Регистрация</h1>
          <p className={s.sub}>Уже есть аккаунт? <Link to="/login">Войти</Link></p>
          {error && <div className={s.error}>{error}</div>}
          <form onSubmit={submit} className={s.form}>
            <div className={s.group}>
              <label>Email</label>
              <input type="email" placeholder="you@example.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} required autoFocus/>
            </div>
            <div className={s.group}>
              <label>Пароль</label>
              <input type="password" placeholder="Минимум 6 символов" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required/>
            </div>
            <div className={s.group}>
              <label>Подтвердите пароль</label>
              <input type="password" placeholder="Повторите пароль" value={form.confirm} onChange={e=>setForm({...form,confirm:e.target.value})} required/>
            </div>
            <button type="submit" className={s.submit} disabled={loading}>{loading?"Регистрация...":"Создать аккаунт"}</button>
          </form>
        </div>
      </div>
    </div>
  );
}
