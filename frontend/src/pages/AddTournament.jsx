import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";
import s from "./AddTournament.module.css";

const CATEGORIES = ["A+100","A+75","B+50","B+30","C+20","C+10"];
const PAIR_COUNTS = [4,6,8,9,10,12,16,20,24,32];

function groupPreview(n) {
  const g = Math.max(2, Math.ceil(n/4));
  const p = Math.ceil(n/g);
  return `${g} группы × ${p} пар`;
}

export default function AddTournament() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title:"", category:"", category_type:"", description:"",
    start_date:"", end_date:"", location:"", total_pairs:"8", bracket_size:"8"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const r = await api.post("/tournaments", { ...form, total_pairs: +form.total_pairs, bracket_size: +form.bracket_size });
      navigate(`/tournaments/${r.data.id}`);
    } catch (err) {
      setError(err.response?.data?.error || "Ошибка создания турнира");
      setLoading(false);
    }
  };

  return (
    <div className={s.root}>
      <div className={s.header}>
        <Link to="/tournaments" className={s.back}>← Турниры</Link>
        <h1 className={s.title}>Создать турнир</h1>
      </div>

      <div className={s.formCard}>
        {error && <div className={s.error}>{error}</div>}
        <form onSubmit={submit}>

          <div className={s.sectionLabel}>Основная информация</div>
          <div className={s.group}><label>Название *</label><input value={form.title} onChange={set("title")} placeholder="Открытый кубок Москвы 2025" required/></div>
          <div className={s.row}>
            <div className={s.group}>
              <label>Категория и очки *</label>
              <select value={form.category} onChange={set("category")} required>
                <option value="">Выберите категорию</option>
                {CATEGORIES.map(c=><option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className={s.group}>
              <label>Тип турнира *</label>
              <select value={form.category_type} onChange={set("category_type")} required>
                <option value="">Выберите тип</option>
                <option value="men_doubles">Мужной парный</option>
                <option value="women_doubles">Женский парный</option>
                <option value="mixed">Микст</option>
                <option value="proam">Про-Ам</option>
              </select>
            </div>
          </div>
          <div className={s.group}><label>Описание</label><textarea rows={4} value={form.description} onChange={set("description")} placeholder="Опишите турнир, правила, призы..."/></div>

          <div className={s.sectionLabel}>Место и время</div>
          <div className={s.group}><label>Место проведения</label><input value={form.location} onChange={set("location")} placeholder='Москва, PadelHub Арена'/></div>
          <div className={s.row}>
            <div className={s.group}><label>Дата начала</label><input type="date" value={form.start_date} onChange={set("start_date")}/></div>
            <div className={s.group}><label>Дата окончания</label><input type="date" value={form.end_date} onChange={set("end_date")}/></div>
          </div>

          <div className={s.sectionLabel}>Формат</div>
          <div className={s.row}>
            <div className={s.group}>
              <label>Количество пар</label>
              <select value={form.total_pairs} onChange={set("total_pairs")}>
                {PAIR_COUNTS.map(n=><option key={n} value={n}>{n} пар</option>)}
              </select>
              <span className={s.hint}>→ {groupPreview(+form.total_pairs)}</span>
            </div>
            <div className={s.group}>
              <label>Размер плей-офф сетки</label>
              <select value={form.bracket_size} onChange={set("bracket_size")}>
                <option value="4">4 (полуфинал)</option>
                <option value="8">8 (четвертьфинал)</option>
                <option value="16">16</option>
                <option value="32">32</option>
              </select>
            </div>
          </div>

          <div className={s.actions}>
            <Link to="/tournaments" className={s.btnGhost}>Отмена</Link>
            <button type="submit" className={s.btnPrimary} disabled={loading}>{loading?"Создание...":"Создать турнир"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
