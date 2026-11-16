import { useState } from "react";
import { ErrorMessage } from "./StatusMessage.jsx";

// Create or edit a plan's basic info (not its drills).
export default function PlanForm({ plan, onSave, onCancel }) {
  const [values, setValues] = useState({
    title: plan?.title ?? "",
    focus: plan?.focus ?? "",
    practice_date: plan?.practice_date ?? "",
    target_minutes: plan?.target_minutes ?? 90,
    notes: plan?.notes ?? "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (field) => (event) => setValues({ ...values, [field]: event.target.value });

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await onSave({
        ...values,
        practice_date: values.practice_date || null,
        target_minutes: Number(values.target_minutes),
      });
    } catch (problem) {
      setError(problem.message);
      setBusy(false);
    }
  }

  return (
    <form className="form card" onSubmit={handleSubmit}>
      <h2>{plan ? "Edit plan" : "New practice plan"}</h2>
      <label>
        Title
        <input value={values.title} onChange={set("title")} maxLength={100} required />
      </label>
      <label>
        Focus <span className="muted">(optional)</span>
        <input value={values.focus} onChange={set("focus")} maxLength={200} placeholder="Serve receive, transition offense…" />
      </label>
      <div className="row">
        <label>
          Date <span className="muted">(optional)</span>
          <input type="date" value={values.practice_date} onChange={set("practice_date")} />
        </label>
        <label>
          Target minutes
          <input type="number" min="15" max="300" value={values.target_minutes} onChange={set("target_minutes")} required />
        </label>
      </div>
      <label>
        Notes <span className="muted">(optional)</span>
        <textarea rows="3" value={values.notes} onChange={set("notes")} maxLength={2000} />
      </label>
      <ErrorMessage message={error} />
      <div className="actions">
        <button className="btn primary" disabled={busy}>{busy ? "Saving…" : "Save plan"}</button>
        <button type="button" className="btn ghost" onClick={onCancel} disabled={busy}>Cancel</button>
      </div>
    </form>
  );
}
