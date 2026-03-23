import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";
import s from "./TournamentDetail.module.css";

const TYPE_LABELS = { men_doubles:"Мужной парный", women_doubles:"Женский парный", mixed:"Микст", proam:"Про-Ам" };
const STATUS_LABELS = { upcoming:"Скоро", active:"Идёт", finished:"Завершён" };
const ROUND_LABELS = { 1:"Финал", 2:"Полуфинал", 3:"Четвертьфинал", 4:"1/8 финала", 5:"1/16 финала" };

export default function TournamentDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [t, setT] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("pairs");
  const [newStatus, setNewStatus] = useState("");
  const [savingStatus, setSavingStatus] = useState(false);

  // Add pair form
  const [showAddPair, setShowAddPair] = useState(false);
  const [pairForm, setPairForm] = useState({ player1_name:"", player2_name:"", group_number:"" });

  // Edit format form
  const [showEditFormat, setShowEditFormat] = useState(false);
  const [fmtForm, setFmtForm] = useState({ num_groups:"", pairs_per_group:"", bracket_size:"" });

  // Score editing state: { [matchId]: { score1, score2 } }
  const [scores, setScores] = useState({});
  const [savingScore, setSavingScore] = useState(null);

  // Bracket score editing
  const [bScores, setBScores] = useState({});
  const [savingBScore, setSavingBScore] = useState(null);

  const [genLoading, setGenLoading] = useState(false);
  const [genBracketLoading, setGenBracketLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);

  const load = () => {
    setLoading(true);
    api.get(`/tournaments/${id}`)
      .then(r => {
        setT(r.data);
        setNewStatus(r.data.status);
        const gf = r.data.group_format || {};
        setFmtForm({
          num_groups: String(gf.groups || 2),
          pairs_per_group: String(gf.pairs_per_group || 4),
          bracket_size: String(r.data.bracket_size || 8),
        });
        // Initialize score state from existing matches
        const sc = {};
        (r.data.group_matches || []).forEach(m => {
          sc[m.id] = { score1: m.score_pair1 || "", score2: m.score_pair2 || "" };
        });
        setScores(sc);
        const bsc = {};
        (r.data.bracket || []).forEach(m => {
          bsc[m.id] = { score1: m.score_pair1 || "", score2: m.score_pair2 || "" };
        });
        setBScores(bsc);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(load, [id]);

  const showMsg = (text, type="success") => {
    setActionMsg({ text, type });
    setTimeout(() => setActionMsg(null), 3000);
  };

  const submitPair = async (e) => {
    e.preventDefault();
    await api.post(`/tournaments/${id}/pairs`, pairForm);
    setPairForm({ player1_name:"", player2_name:"", group_number:"" });
    setShowAddPair(false);
    load();
  };

  const deletePair = async (pid) => {
    if (!confirm("Удалить пару?")) return;
    await api.delete(`/tournaments/${id}/pairs/${pid}`);
    load();
  };

  const updateStatus = async () => {
    setSavingStatus(true);
    await api.put(`/tournaments/${id}/status`, { status: newStatus });
    setSavingStatus(false);
    load();
  };

  const updateFormat = async (e) => {
    e.preventDefault();
    await api.put(`/tournaments/${id}/format`, {
      num_groups: +fmtForm.num_groups,
      pairs_per_group: +fmtForm.pairs_per_group,
      bracket_size: +fmtForm.bracket_size,
    });
    setShowEditFormat(false);
    showMsg("Формат обновлён");
    load();
  };

  const generateMatches = async () => {
    setGenLoading(true);
    try {
      const r = await api.post(`/tournaments/${id}/group_matches/generate`);
      showMsg(`Сгенерировано ${r.data.generated} матчей`);
      load();
    } catch (e) {
      showMsg(e.response?.data?.error || "Ошибка", "error");
    } finally { setGenLoading(false); }
  };

  const saveGroupScore = async (mid) => {
    setSavingScore(mid);
    try {
      await api.put(`/tournaments/${id}/group_matches/${mid}/score`, {
        score_pair1: scores[mid]?.score1 || "",
        score_pair2: scores[mid]?.score2 || "",
      });
      showMsg("Счёт сохранён");
      load();
    } catch { showMsg("Ошибка сохранения", "error"); }
    finally { setSavingScore(null); }
  };

  const generateBracket = async () => {
    setGenBracketLoading(true);
    try {
      const r = await api.post(`/tournaments/${id}/bracket/generate`);
      showMsg(`Сетка сформирована. Вышло ${r.data.advancers} пар`);
      setTab("bracket");
      load();
    } catch (e) {
      showMsg(e.response?.data?.error || "Ошибка", "error");
    } finally { setGenBracketLoading(false); }
  };

  const saveBracketScore = async (mid) => {
    setSavingBScore(mid);
    try {
      await api.put(`/tournaments/${id}/bracket/${mid}/score`, {
        score_pair1: bScores[mid]?.score1 || "",
        score_pair2: bScores[mid]?.score2 || "",
      });
      showMsg("Счёт сохранён");
      load();
    } catch { showMsg("Ошибка сохранения", "error"); }
    finally { setSavingBScore(null); }
  };

  if (loading) return <div style={{display:"flex",justifyContent:"center",padding:"4rem"}}><div className="loader"/></div>;
  if (!t) return <div className={s.notFound}><h2>Турнир не найден</h2><Link to="/tournaments">← Назад</Link></div>;

  const gf = t.group_format || {};

  // Build groups map
  const groups = {};
  (t.pairs || []).forEach(p => {
    const g = p.group_number || 0;
    if (!groups[g]) groups[g] = [];
    groups[g].push(p);
  });

  // Build group standings
  const standingsMap = {};
  (t.pairs || []).forEach(p => {
    standingsMap[p.id] = { pair: p, wins: 0, losses: 0, played: 0 };
  });
  (t.group_matches || []).forEach(m => {
    if (!m.winner_pair_id) return;
    const loserId = m.winner_pair_id === m.pair1_id ? m.pair2_id : m.pair1_id;
    if (standingsMap[m.winner_pair_id]) { standingsMap[m.winner_pair_id].wins++; standingsMap[m.winner_pair_id].played++; }
    if (standingsMap[loserId]) { standingsMap[loserId].losses++; standingsMap[loserId].played++; }
  });

  // Build bracket rounds
  const bracketByRound = {};
  (t.bracket || []).forEach(m => {
    if (!bracketByRound[m.round]) bracketByRound[m.round] = [];
    bracketByRound[m.round].push(m);
  });
  const rounds = Object.keys(bracketByRound).map(Number).sort((a,b) => b - a);

  const pairLabel = (p) => p ? `${p.player1_name}${p.player2_name ? " / " + p.player2_name : ""}` : "TBD";

  return (
    <div className={s.root}>
      {/* Header */}
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
            <button className={s.btnOutline} onClick={updateStatus} disabled={savingStatus}>{savingStatus?"...":"Обновить статус"}</button>
          </div>
        )}
      </div>

      {actionMsg && <div className={actionMsg.type==="error" ? s.msgError : s.msgSuccess}>{actionMsg.text}</div>}

      {t.description && <p className={s.desc}>{t.description}</p>}

      {/* Info cards */}
      <div className={s.infoCards}>
        {t.start_date && <div className={s.infoCard}><span>Начало</span><strong>{new Date(t.start_date).toLocaleDateString("ru")}</strong></div>}
        {t.end_date && <div className={s.infoCard}><span>Конец</span><strong>{new Date(t.end_date).toLocaleDateString("ru")}</strong></div>}
        {t.location && <div className={s.infoCard}><span>Место</span><strong>{t.location}</strong></div>}
        {gf.groups && <div className={s.infoCard}><span>Групп</span><strong>{gf.groups}</strong></div>}
        {gf.pairs_per_group && <div className={s.infoCard}><span>Пар в группе</span><strong>{gf.pairs_per_group}</strong></div>}
        {gf.total_pairs && <div className={s.infoCard}><span>Всего пар</span><strong>{gf.total_pairs}</strong></div>}
        <div className={s.infoCard}><span>Сетка</span><strong>{t.bracket_size}</strong></div>
        {user?.is_superuser && (
          <button className={s.infoCardBtn} onClick={() => setShowEditFormat(v=>!v)}>✏️ Изменить формат</button>
        )}
      </div>

      {/* Edit format panel */}
      {showEditFormat && user?.is_superuser && (
        <form onSubmit={updateFormat} className={s.editFormatPanel}>
          <h4>Изменить формат</h4>
          <div className={s.editFmtRow}>
            <div className={s.formGroup}>
              <label>Групп</label>
              <input type="number" min="1" max="16" value={fmtForm.num_groups} onChange={e=>setFmtForm(f=>({...f,num_groups:e.target.value}))}/>
            </div>
            <div className={s.formGroup}>
              <label>Пар в группе</label>
              <input type="number" min="2" max="12" value={fmtForm.pairs_per_group} onChange={e=>setFmtForm(f=>({...f,pairs_per_group:e.target.value}))}/>
            </div>
            <div className={s.formGroup}>
              <label>Размер сетки</label>
              <select value={fmtForm.bracket_size} onChange={e=>setFmtForm(f=>({...f,bracket_size:e.target.value}))}>
                {[2,4,8,16,32].map(n=><option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <button type="submit" className={s.btnPrimary}>Сохранить</button>
            <button type="button" className={s.btnGhost} onClick={()=>setShowEditFormat(false)}>Отмена</button>
          </div>
          <small className={s.fmtHint}>Итого пар: {+fmtForm.num_groups * +fmtForm.pairs_per_group}</small>
        </form>
      )}

      {/* Tabs */}
      <div className={s.tabs}>
        {[["pairs","Участники"],["groups","Групповой этап"],["bracket","Сетка плей-офф"]].map(([k,l])=>(
          <button key={k} className={`${s.tab} ${tab===k?s.tabActive:""}`} onClick={()=>setTab(k)}>{l}</button>
        ))}
      </div>

      {/* ── PAIRS TAB ── */}
      {tab==="pairs" && (
        <div>
          <div className={s.tabHeader}>
            <h2 className={s.sectionTitle}>Участники ({(t.pairs||[]).length})</h2>
            {user?.is_superuser && <button className={s.btnOutline} onClick={()=>setShowAddPair(v=>!v)}>+ Добавить пару</button>}
          </div>
          {showAddPair && user?.is_superuser && (
            <form onSubmit={submitPair} className={s.addForm}>
              <div className={s.addFormRow}>
                <div className={s.formGroup}><label>Игрок 1 / Пара</label><input value={pairForm.player1_name} onChange={e=>setPairForm(f=>({...f,player1_name:e.target.value}))} placeholder="Иванов А.П." required/></div>
                <div className={s.formGroup}><label>Игрок 2</label><input value={pairForm.player2_name} onChange={e=>setPairForm(f=>({...f,player2_name:e.target.value}))} placeholder="Петров С.В."/></div>
                <div className={s.formGroup}>
                  <label>Группа №</label>
                  <select value={pairForm.group_number} onChange={e=>setPairForm(f=>({...f,group_number:e.target.value}))}>
                    <option value="">Без группы</option>
                    {Array.from({length: gf.groups || 2}, (_,i)=>i+1).map(n=>(
                      <option key={n} value={n}>Группа {n}</option>
                    ))}
                  </select>
                </div>
                <button type="submit" className={s.btnPrimary}>Добавить</button>
              </div>
            </form>
          )}
          {(t.pairs||[]).length > 0 ? (
            <div className={s.tableWrap}>
              <table className={s.table}>
                <thead><tr><th>#</th><th>Пара</th><th>Группа</th>{user?.is_superuser && <th></th>}</tr></thead>
                <tbody>
                  {(t.pairs||[]).map((p,i) => (
                    <tr key={p.id}>
                      <td className={s.tdNum}>{i+1}</td>
                      <td><strong>{p.player1_name}</strong>{p.player2_name && <> / {p.player2_name}</>}</td>
                      <td>{p.group_number ? `Группа ${p.group_number}` : "—"}</td>
                      {user?.is_superuser && (
                        <td><button className={s.btnDel} onClick={()=>deletePair(p.id)}>✕</button></td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <div className={s.empty}>Участники ещё не добавлены</div>}
        </div>
      )}

      {/* ── GROUPS TAB ── */}
      {tab==="groups" && (
        <div>
          <div className={s.tabHeader}>
            <h2 className={s.sectionTitle}>Групповой этап</h2>
            {user?.is_superuser && (
              <div className={s.btnGroup}>
                <button className={s.btnOutline} onClick={generateMatches} disabled={genLoading}>
                  {genLoading ? "..." : "⚙ Сгенерировать матчи"}
                </button>
                <button className={s.btnPrimary} onClick={generateBracket} disabled={genBracketLoading}>
                  {genBracketLoading ? "..." : "→ Сформировать сетку"}
                </button>
              </div>
            )}
          </div>

          {Object.keys(groups).filter(g=>+g>0).length > 0 ? (
            Object.entries(groups).filter(([g])=>+g>0).sort(([a],[b])=>+a-+b).map(([gNum, pairs]) => {
              const gMatches = (t.group_matches||[]).filter(m => m.group_number === +gNum);
              const standing = pairs
                .map(p => standingsMap[p.id] || {pair:p, wins:0, losses:0, played:0})
                .sort((a,b) => b.wins - a.wins);

              return (
                <div key={gNum} className={s.groupBlock}>
                  <h3 className={s.groupTitle}>Группа {gNum}</h3>
                  <div className={s.groupLayout}>
                    {/* Standing table */}
                    <div className={s.standingWrap}>
                      <div className={s.standingLabel}>Турнирная таблица</div>
                      <table className={s.standingTable}>
                        <thead><tr><th>#</th><th>Пара</th><th>И</th><th>В</th><th>П</th></tr></thead>
                        <tbody>
                          {standing.map((row, i) => (
                            <tr key={row.pair.id} className={i===0 && row.played>0 ? s.leader : ""}>
                              <td>{i+1}</td>
                              <td>{pairLabel(row.pair)}</td>
                              <td>{row.played}</td>
                              <td className={s.wins}>{row.wins}</td>
                              <td className={s.losses}>{row.losses}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Matches */}
                    {gMatches.length > 0 && (
                      <div className={s.matchesWrap}>
                        <div className={s.standingLabel}>Матчи</div>
                        {gMatches.map(m => (
                          <div key={m.id} className={`${s.matchRow} ${m.winner_pair_id ? s.matchPlayed : ""}`}>
                            <div className={s.matchPairs}>
                              <span className={m.winner_pair_id===m.pair1_id ? s.matchWinner : ""}>{m.p1_name}{m.p1_name2?" / "+m.p1_name2:""}</span>
                              <span className={s.vs}>vs</span>
                              <span className={m.winner_pair_id===m.pair2_id ? s.matchWinner : ""}>{m.p2_name}{m.p2_name2?" / "+m.p2_name2:""}</span>
                            </div>
                            {user?.is_superuser ? (
                              <div className={s.scoreEntry}>
                                <input
                                  className={s.scoreInput}
                                  value={scores[m.id]?.score1 ?? ""}
                                  onChange={e => setScores(sc => ({...sc, [m.id]: {...(sc[m.id]||{}), score1: e.target.value}}))}
                                  placeholder="6:3 6:4"
                                />
                                <span className={s.scoreSep}>:</span>
                                <input
                                  className={s.scoreInput}
                                  value={scores[m.id]?.score2 ?? ""}
                                  onChange={e => setScores(sc => ({...sc, [m.id]: {...(sc[m.id]||{}), score2: e.target.value}}))}
                                  placeholder="3:6 4:6"
                                />
                                <button
                                  className={s.btnSave}
                                  onClick={() => saveGroupScore(m.id)}
                                  disabled={savingScore === m.id}
                                >{savingScore===m.id?"...":"✓"}</button>
                              </div>
                            ) : (
                              <div className={s.scoreDisplay}>
                                {m.score_pair1 && m.score_pair2
                                  ? <><span>{m.score_pair1}</span><span className={s.scoreSep}>:</span><span>{m.score_pair2}</span></>
                                  : <span className={s.noScore}>—</span>}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          ) : <div className={s.empty}>
            Сначала добавьте участников и назначьте им группы, затем нажмите «Сгенерировать матчи»
          </div>}
        </div>
      )}

      {/* ── BRACKET TAB ── */}
      {tab==="bracket" && (
        <div>
          <div className={s.tabHeader}>
            <h2 className={s.sectionTitle}>Сетка плей-офф (на {t.bracket_size})</h2>
            {user?.is_superuser && (
              <button className={s.btnPrimary} onClick={generateBracket} disabled={genBracketLoading}>
                {genBracketLoading ? "..." : "⚙ Пересформировать сетку"}
              </button>
            )}
          </div>
          {rounds.length > 0 ? (
            <div className={s.bracket}>
              {rounds.map(r => (
                <div key={r} className={s.bracketRound}>
                  <div className={s.roundLabel}>{ROUND_LABELS[r] || `Раунд ${r}`}</div>
                  {bracketByRound[r].sort((a,b)=>a.match_number-b.match_number).map(m => {
                    const p1 = (t.pairs||[]).find(p=>p.id===m.pair1_id);
                    const p2 = (t.pairs||[]).find(p=>p.id===m.pair2_id);
                    return (
                      <div key={m.id} className={s.bracketMatch}>
                        <div className={`${s.bracketPair} ${m.winner_pair_id===m.pair1_id?s.bWinner:""}`}>
                          <span>{p1 ? pairLabel(p1) : "TBD"}</span>
                          <span className={s.bScore}>{m.score_pair1||""}</span>
                        </div>
                        <div className={`${s.bracketPair} ${m.winner_pair_id===m.pair2_id?s.bWinner:""}`}>
                          <span>{p2 ? pairLabel(p2) : "TBD"}</span>
                          <span className={s.bScore}>{m.score_pair2||""}</span>
                        </div>
                        {user?.is_superuser && (m.pair1_id || m.pair2_id) && (
                          <div className={s.bScoreEntry}>
                            <input className={s.bScoreInput} value={bScores[m.id]?.score1??""} placeholder="6:3" onChange={e=>setBScores(bs=>({...bs,[m.id]:{...(bs[m.id]||{}),score1:e.target.value}}))}/>
                            <span>:</span>
                            <input className={s.bScoreInput} value={bScores[m.id]?.score2??""} placeholder="3:6" onChange={e=>setBScores(bs=>({...bs,[m.id]:{...(bs[m.id]||{}),score2:e.target.value}}))}/>
                            <button className={s.btnSave} onClick={()=>saveBracketScore(m.id)} disabled={savingBScore===m.id}>{savingBScore===m.id?"...":"✓"}</button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          ) : (
            <div className={s.empty}>
              Сетка ещё не сформирована.
              {user?.is_superuser && <> После завершения группового этапа нажмите «Сформировать сетку» на вкладке «Групповой этап».</>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
