import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";
import s from "./AddTournament.module.css";

const CATEGORIES = ["A+100","A+75","B+50","B+30","C+20","C+10"];

export default function AddTournament() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title:"", category:"", category_type:"", description:"",
    start_date:"", end_date:"", location:"",
    num_groups:"2", pairs_per_group:"4", bracket_size:"8"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }));

  const totalPairs = +form.num_groups * +form.pairs_per_group;
  const minBracket = Math.pow(2, Math.ceil(Math.log2(+form.num_groups || 2)));

  const submit = async (e) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const r = await api.post("/tournaments", {
        ...form,
        num_groups: +form.num_groups,
        pairs_per_group: +form.pairs_per_group,
        bracket_size: +form.bracket_size,
      });
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
          <div className={s.group}><label>Место проведения</label><input value={form.location} onChange={set("location")} placeholder="Москва, PadelHub Арена"/></div>
          <div className={s.row}>
            <div className={s.group}><label>Дата начала</label><input type="date" value={form.start_date} onChange={set("start_date")}/></div>
            <div className={s.group}><label>Дата окончания</label><input type="date" value={form.end_date} onChange={set("end_date")}/></div>
          </div>

          <div className={s.sectionLabel}>Формат</div>
          <div className={s.formatNote}>
            Задайте количество групп и пар в каждой группе. Итого участников: <strong>{totalPairs}</strong>.
            После регистрации параметры можно изменить на странице турнира.
          </div>
          <div className={s.row}>
            <div className={s.group}>
              <label>Количество групп</label>
              <input type="number" min="1" max="16" value={form.num_groups} onChange={set("num_groups")}/>
            </div>
            <div className={s.group}>
              <label>Пар в каждой группе</label>
              <input type="number" min="2" max="12" value={form.pairs_per_group} onChange={set("pairs_per_group")}/>
            </div>
          </div>
          <div className={s.row}>
            <div className={s.group}>
              <label>Размер плей-офф сетки</label>
              <select value={form.bracket_size} onChange={set("bracket_size")}>
                {[2,4,8,16,32].filter(n => n >= minBracket).map(n => (
                  <option key={n} value={n}>{n} {n===2?"(финал)":n===4?"(полуфинал)":n===8?"(четвертьфинал)":""}</option>
                ))}
              </select>
              <span className={s.hint}>Минимум {minBracket} — по одному победителю из каждой группы</span>
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
