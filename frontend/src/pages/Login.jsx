import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import s from "./Auth.module.css";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Ошибка входа");
    } finally { setLoading(false); }
  };

  return (
    <div className={s.split}>
      <div className={s.visual}>
        <Link to="/" className={s.logo}><span className={s.logoIcon}>◈</span><span className={s.logoText}>PADEL<em>HUB</em></span></Link>
        <div className={s.visualText}><h2>Добро<br/>пожаловать<br/>обратно</h2><p>Войди, чтобы следить за турнирами и рейтингом</p></div>
        <div className={s.decoCircle1}/><div className={s.decoCircle2}/><div className={s.decoNet}/>
      </div>
      <div className={s.formSide}>
        <div className={s.formWrap}>
          <h1 className={s.title}>Вход</h1>
          <p className={s.sub}>Нет аккаунта? <Link to="/register">Зарегистрируйся</Link></p>
          {error && <div className={s.error}>{error}</div>}
          <form onSubmit={submit} className={s.form}>
            <div className={s.group}>
              <label>Email</label>
              <input type="email" placeholder="you@example.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} required autoFocus/>
            </div>
            <div className={s.group}>
              <label>Пароль</label>
              <input type="password" placeholder="••••••••" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required/>
            </div>
            <button type="submit" className={s.submit} disabled={loading}>{loading?"Вход...":"Войти"}</button>
          </form>
        </div>
      </div>
    </div>
  );
}
