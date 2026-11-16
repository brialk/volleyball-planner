import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";
import { useLoad } from "../hooks.js";
import { categoryClass, formatDate } from "../utils.js";
import PlanForm from "../components/PlanForm.jsx";
import TimeBar from "../components/TimeBar.jsx";
import ConfirmButton from "../components/ConfirmButton.jsx";
import { Empty, ErrorMessage, Loading } from "../components/StatusMessage.jsx";

// One row in the plan. Minutes and notes can be edited in place.
function PlanItemRow({ item, index, count, busy, onSave, onMove, onRemove }) {
  const [minutes, setMinutes] = useState(item.minutes);
  const [notes, setNotes] = useState(item.notes);
  const changed = Number(minutes) !== item.minutes || notes !== item.notes;

  return (
    <li className="card item">
      <div className="item-top">
        <span className="step">{index + 1}</span>
        <div className="item-title">
          <h3>{item.drill.name}</h3>
          <div className="tags">
            <span className={`tag ${categoryClass(item.drill.category)}`}>{item.drill.category}</span>
            <span className="tag level">{item.drill.skill_level}</span>
          </div>
        </div>
        <div className="move">
          <button className="btn ghost small" aria-label={`Move ${item.drill.name} up`} disabled={busy || index === 0} onClick={() => onMove(index, -1)}>↑</button>
          <button className="btn ghost small" aria-label={`Move ${item.drill.name} down`} disabled={busy || index === count - 1} onClick={() => onMove(index, 1)}>↓</button>
        </div>
      </div>
      <div className="row item-edit">
        <label>
          Minutes
          <input type="number" min="1" max="180" value={minutes} onChange={(e) => setMinutes(e.target.value)} />
        </label>
        <label className="grow">
          Notes
          <input value={notes} maxLength={300} onChange={(e) => setNotes(e.target.value)} placeholder="Coaching cues for this block" />
        </label>
      </div>
      <div className="actions">
        <button className="btn small primary" disabled={!changed || busy} onClick={() => onSave(item, { minutes: Number(minutes), notes })}>
          Save changes
        </button>
        <ConfirmButton label="Remove" disabled={busy} onConfirm={() => onRemove(item)} />
      </div>
    </li>
  );
}

export default function PlanDetailPage() {
  const { planId } = useParams();
  const navigate = useNavigate();
  const plan = useLoad(() => api.getPlan(planId), [planId]);
  const drills = useLoad(() => api.getDrills(), []);
  const [editing, setEditing] = useState(false);
  const [pick, setPick] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");

  // Runs a plan-changing request, then shows the plan the server sends back.
  async function run(action) {
    setActionError("");
    setBusy(true);
    try {
      const data = await action();
      if (data?.plan) plan.setData(data);
      return true;
    } catch (problem) {
      setActionError(problem.message);
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function savePlan(values) {
    const data = await api.updatePlan(planId, values);
    plan.setData(data);
    setEditing(false);
  }

  async function deletePlan() {
    setActionError("");
    try {
      await api.deletePlan(planId);
      navigate("/plans");
    } catch (problem) {
      setActionError(problem.message);
    }
  }

  async function addDrill(event) {
    event.preventDefault();
    if (!pick) return;
    const ok = await run(() => api.addPlanItem(planId, { drill_id: Number(pick) }));
    if (ok) setPick("");
  }

  function move(index, direction) {
    const ids = plan.data.plan.items.map((item) => item.id);
    const target = index + direction;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    run(() => api.reorderPlanItems(planId, ids));
  }

  if (plan.loading && !plan.data) return <Loading text="Loading plan…" />;
  if (plan.error) {
    return (
      <>
        <ErrorMessage message={plan.error} onRetry={plan.reload} />
        <Link to="/plans">← Back to plans</Link>
      </>
    );
  }

  const p = plan.data.plan;

  return (
    <section>
      <Link to="/plans" className="back">← All plans</Link>

      {editing ? (
        <PlanForm plan={p} onSave={savePlan} onCancel={() => setEditing(false)} />
      ) : (
        <div className="card plan-head">
          <p className="muted small-text">{formatDate(p.practice_date)}</p>
          <h1>{p.title}</h1>
          {p.focus && <p>{p.focus}</p>}
          {p.notes && <p className="muted">{p.notes}</p>}
          <TimeBar total={p.total_minutes} target={p.target_minutes} />
          <div className="actions">
            <button className="btn small" onClick={() => setEditing(true)}>Edit plan</button>
            <ConfirmButton label="Delete plan" onConfirm={deletePlan} />
          </div>
        </div>
      )}

      <ErrorMessage message={actionError} />

      <h2>Drills in this plan</h2>
      <form className="add-drill card" onSubmit={addDrill}>
        <label className="grow">
          Add a drill
          <select value={pick} onChange={(e) => setPick(e.target.value)} disabled={!drills.data}>
            <option value="">{drills.loading ? "Loading your drills…" : "Choose a drill…"}</option>
            {drills.data?.drills.map((d) => (
              <option key={d.id} value={d.id}>{d.name} ({d.default_minutes} min)</option>
            ))}
          </select>
        </label>
        <button className="btn primary" disabled={!pick || busy}>Add to plan</button>
      </form>
      <ErrorMessage message={drills.error} onRetry={drills.reload} />
      {drills.data && drills.data.drills.length === 0 && (
        <p className="muted">You have no drills yet. <Link to="/drills">Create one first.</Link></p>
      )}

      {p.items.length === 0 ? (
        <Empty title="This plan is empty">
          <p className="muted">Pick a drill above to build your practice.</p>
        </Empty>
      ) : (
        <ol className="items">
          {p.items.map((item, index) => (
            <PlanItemRow
              key={item.id}
              item={item}
              index={index}
              count={p.items.length}
              busy={busy}
              onSave={(it, changes) => run(() => api.updatePlanItem(planId, it.id, changes))}
              onMove={move}
              onRemove={(it) => run(() => api.deletePlanItem(planId, it.id))}
            />
          ))}
        </ol>
      )}
    </section>
  );
}
