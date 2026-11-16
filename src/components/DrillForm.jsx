import { useState } from "react";
import { ErrorMessage } from "./StatusMessage.jsx";

const EMPTY = {
  name: "",
  description: "",
  category: "Warm-up",
  skill_level: "Beginner",
  default_minutes: 10,
  equipment: "",
};

// Used for both "new drill" and "edit drill". Pass `drill` to edit.
export default function DrillForm({ drill, options, onSave, onCancel }) {
  const [values, setValues] = useState(drill ? { ...EMPTY, ...drill } : EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (field) => (event) => setValues({ ...values, [field]: event.target.value });

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await onSave({ ...values, default_minutes: Number(values.default_minutes) });
    } catch (problem) {
      setError(problem.message);
      setBusy(false);
    }
  }

  return (
    <form className="form card" onSubmit={handleSubmit}>
      <h2>{drill ? "Edit drill" : "New drill"}</h2>
      <label>
        Name
        <input value={values.name} onChange={set("name")} maxLength={80} required />
      </label>
      <div className="row">
        <label>
          Category
          <select value={values.category} onChange={set("category")}>
            {options.categories.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <label>
          Skill level
          <select value={values.skill_level} onChange={set("skill_level")}>
            {options.skill_levels.map((l) => <option key={l}>{l}</option>)}
          </select>
        </label>
        <label>
          Minutes
          <input type="number" min="1" max="180" value={values.default_minutes} onChange={set("default_minutes")} required />
        </label>
      </div>
      <label>
        Equipment <span className="muted">(optional)</span>
        <input value={values.equipment} onChange={set("equipment")} maxLength={120} placeholder="Balls, cones, net…" />
      </label>
      <label>
        How it works <span className="muted">(optional)</span>
        <textarea rows="4" value={values.description} onChange={set("description")} maxLength={1000} />
      </label>
      <ErrorMessage message={error} />
      <div className="actions">
        <button className="btn primary" disabled={busy}>{busy ? "Saving…" : "Save drill"}</button>
        <button type="button" className="btn ghost" onClick={onCancel} disabled={busy}>Cancel</button>
      </div>
    </form>
  );
}
