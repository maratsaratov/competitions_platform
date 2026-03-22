import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";
import s from "./TournamentDetail.module.css";

const TYPE_LABELS = { men_doubles:"Мужной парный", women_doubles:"Женский парный", mixed:"Микст", proam:"Про-Ам" };
const STATUS_LABELS = { upcoming:"Скоро", active:"Идёт", finished:"Завершён" };
const ROUND_LABELS = { 1:"Финал", 2:"Полуфинал", 3:"Четвертьфинал" };

export default function TournamentDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [t, setT] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("pairs");
  const [addPairForm, setAddPairForm] = useState({ player1_name:"", player2_name:"", group_number:"" });
  const [showAddPair, setShowAddPair] = useState(false);
  const [newStatus, setNewStatus] = useState("");
  const [savingStatus, setSavingStatus] = useState(false);

  const load = () => {
    setLoading(true);
    api.get(`/tournaments/${id}`).then(r => { setT(r.data); setNewStatus(r.data.status); setLoading(false); }).catch(()=>setLoading(false));
  };
  useEffect(load, [id]);

  const submitPair = async (e) => {
    e.preventDefault();
    await api.post(`/tournaments/${id}/pairs`, addPairForm);
    setAddPairForm({ player1_name:"", player2_name:"", group_number:"" });
    setShowAddPair(false);
    load();
  };

  const updateStatus = async () => {
    setSavingStatus(true);
    await api.put(`/tournaments/${id}/status`, { status: newStatus });
    setSavingStatus(false);
    load();
  };

  if (loading) return <div style={{display:"flex",justifyContent:"center",padding:"4rem"}}><div className="loader"/></div>;
  if (!t) return <div className={s.notFound}><h2>Турнир не найден</h2><Link to="/tournaments">← Назад</Link></div>;

  // Group pairs by group_number
  const groups = {};
  (t.pairs||[]).forEach(p => {
    const g = p.group_number || 0;
    if (!groups[g]) groups[g] = [];
    groups[g].push(p);
  });

  // Group bracket by round
  const bracketByRound = {};
  (t.bracket||[]).forEach(m => {
    if (!bracketByRound[m.round]) bracketByRound[m.round] = [];
    bracketByRound[m.round].push(m);
  });
  const rounds = Object.keys(bracketByRound).map(Number).sort((a,b)=>b-a);

  return (
    <div className={s.root}>
      <div className={s.header}>
        <div>
          <Link to="/tournaments" className={s.back}>← Все турниры</Link>
          <h1 className={s.title}>{t.title}</h1>
          <div className={s.badges}>
            <span className={`${s.typeBadge} ${s["type_"+t.category_type]}`}>{TYPE_LABELS[t.category_type]}</span>
            <span className={s.categoryTag}>{t.category}</span>
            <span className={`${s.statusBadge} ${s["status_"+t.status]}`}>{STATUS_LABELS[t.status]}</span>
          </div>
        </div>
        {user?.is_superuser && (
          <div className={s.adminCtrl}>
            <select value={newStatus} onChange={e=>setNewStatus(e.target.value)} className={s.select}>
              <option value="upcoming">Скоро</option>
              <option value="active">Идёт</option>
              <option value="finished">Завершён</option>
            </select>
            <button className={s.btnOutline} onClick={updateStatus} disabled={savingStatus}>{savingStatus?"...":"Обновить"}</button>
          </div>
        )}
      </div>

      {t.description && <p className={s.desc}>{t.description}</p>}

      <div className={s.infoCards}>
        {t.start_date && <div className={s.infoCard}><span>Начало</span><strong>{new Date(t.start_date).toLocaleDateString("ru")}</strong></div>}
        {t.end_date && <div className={s.infoCard}><span>Конец</span><strong>{new Date(t.end_date).toLocaleDateString("ru")}</strong></div>}
        {t.location && <div className={s.infoCard}><span>Место</span><strong>{t.location}</strong></div>}
        {t.group_format && <>
          <div className={s.infoCard}><span>Групп</span><strong>{t.group_format.groups} × {t.group_format.pairs_per_group} пары</strong></div>
          <div className={s.infoCard}><span>Пар</span><strong>{t.group_format.total_pairs}</strong></div>
        </>}
        <div className={s.infoCard}><span>Сетка</span><strong>{t.bracket_size}</strong></div>
      </div>

      <div className={s.tabs}>
        {[["pairs","Участники"],["groups","Групповой этап"],["bracket","Сетка"]].map(([k,l])=>(
          <button key={k} className={`${s.tab} ${tab===k?s.tabActive:""}`} onClick={()=>setTab(k)}>{l}</button>
        ))}
      </div>

      {tab==="pairs" && (
        <div>
          <div className={s.tabHeader}>
            <h2 className={s.sectionTitle}>Участники ({(t.pairs||[]).length})</h2>
            {user?.is_superuser && <button className={s.btnOutline} onClick={()=>setShowAddPair(v=>!v)}>+ Добавить пару</button>}
          </div>
          {showAddPair && user?.is_superuser && (
            <form onSubmit={submitPair} className={s.addForm}>
              <div className={s.addFormRow}>
                <div className={s.formGroup}><label>Игрок 1 / Пара</label><input value={addPairForm.player1_name} onChange={e=>setAddPairForm(f=>({...f,player1_name:e.target.value}))} placeholder="Иванов А.П." required/></div>
                <div className={s.formGroup}><label>Игрок 2</label><input value={addPairForm.player2_name} onChange={e=>setAddPairForm(f=>({...f,player2_name:e.target.value}))} placeholder="Петров С.В."/></div>
                <div className={s.formGroup}><label>Группа №</label><input type="number" min="1" value={addPairForm.group_number} onChange={e=>setAddPairForm(f=>({...f,group_number:e.target.value}))} placeholder="1"/></div>
                <button type="submit" className={s.btnPrimary}>Добавить</button>
              </div>
            </form>
          )}
          {(t.pairs||[]).length > 0 ? (
            <div className={s.tableWrap}>
              <table className={s.table}>
                <thead><tr><th>#</th><th>Пара</th><th>Группа</th></tr></thead>
                <tbody>
                  {(t.pairs||[]).map((p,i)=>(
                    <tr key={p.id}>
                      <td className={s.tdNum}>{i+1}</td>
                      <td><strong>{p.player1_name}</strong>{p.player2_name&&<> / {p.player2_name}</>}</td>
                      <td>{p.group_number ? `Группа ${p.group_number}` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <div className={s.empty}>Участники ещё не добавлены</div>}
        </div>
      )}

      {tab==="groups" && (
        <div>
          <h2 className={s.sectionTitle}>Групповой этап</h2>
          {Object.keys(groups).filter(g=>g>0).length > 0 ? (
            Object.entries(groups).filter(([g])=>g>0).sort(([a],[b])=>a-b).map(([gNum, pairs])=>{
              const gMatches = (t.group_matches||[]).filter(m=>m.group_number===+gNum);
              return (
                <div key={gNum} className={s.groupBlock}>
                  <h3 className={s.groupTitle}>Группа {gNum}</h3>
                  <div className={s.groupPairs}>
                    {pairs.map((p,i)=>(
                      <div key={p.id} className={s.groupPair}>
                        <span className={s.pairNum}>{i+1}</span>
                        <span>{p.player1_name}{p.player2_name&&` / ${p.player2_name}`}</span>
                      </div>
                    ))}
                  </div>
                  {gMatches.length>0 && (
                    <div className={s.tableWrap} style={{marginTop:"1rem"}}>
                      <table className={s.table}>
                        <thead><tr><th>Пара 1</th><th>Счёт</th><th>Пара 2</th><th>Счёт</th></tr></thead>
                        <tbody>
                          {gMatches.map(m=>(
                            <tr key={m.id}>
                              <td>{m.p1_name||"—"}</td><td>{m.score_pair1||"—"}</td>
                              <td>{m.p2_name||"—"}</td><td>{m.score_pair2||"—"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })
          ) : <div className={s.empty}>Группы ещё не сформированы. Добавьте участников и назначьте им группы.</div>}
        </div>
      )}

      {tab==="bracket" && (
        <div>
          <h2 className={s.sectionTitle}>Сетка плей-офф (на {t.bracket_size})</h2>
          {rounds.length > 0 ? (
            <div className={s.bracket}>
              {rounds.map(r=>(
                <div key={r} className={s.bracketRound}>
                  <div className={s.roundLabel}>{ROUND_LABELS[r]||`Раунд ${r}`}</div>
                  {bracketByRound[r].map(m=>(
                    <div key={m.id} className={s.bracketMatch}>
                      <div className={`${s.bracketPair} ${m.winner_pair_id===m.pair1_id?s.winner:""}`}>
                        <span>{m.p1_name||"TBD"}</span>
                        <span className={s.bScore}>{m.score_pair1||""}</span>
                      </div>
                      <div className={`${s.bracketPair} ${m.winner_pair_id===m.pair2_id?s.winner:""}`}>
                        <span>{m.p2_name||"TBD"}</span>
                        <span className={s.bScore}>{m.score_pair2||""}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : <div className={s.empty}>Сетка будет сформирована после группового этапа</div>}
        </div>
      )}
    </div>
  );
}
