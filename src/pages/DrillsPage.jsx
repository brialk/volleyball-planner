import { useState } from "react";
import { api } from "../api.js";
import { useLoad, useDebounced } from "../hooks.js";
import { categoryClass } from "../utils.js";
import DrillForm from "../components/DrillForm.jsx";
import ConfirmButton from "../components/ConfirmButton.jsx";
import { Empty, ErrorMessage, Loading } from "../components/StatusMessage.jsx";

export default function DrillsPage() {
  const [category, setCategory] = useState("");
  const [level, setLevel] = useState("");
  const [search, setSearch] = useState("");
  const q = useDebounced(search, 300);
  const [editing, setEditing] = useState(null); // null = hidden, "new" = create, or a drill
  const [actionError, setActionError] = useState("");

  const options = useLoad(() => api.getDrillOptions(), []);
  const drills = useLoad(
    () => api.getDrills({ category, skill_level: level, q }),
    [category, level, q]
  );

  async function save(values) {
    if (editing === "new") await api.createDrill(values);
    else await api.updateDrill(editing.id, values);
    setEditing(null);
    drills.reload();
  }

  async function remove(drill) {
    setActionError("");
    try {
      await api.deleteDrill(drill.id);
      drills.reload();
    } catch (problem) {
      setActionError(problem.message);
    }
  }

  const filtersOn = category || level || q;

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Drill library</h1>
          <p className="muted">Your reusable drills. Add them to any practice plan.</p>
        </div>
        {!editing && options.data && (
          <button className="btn primary" onClick={() => setEditing("new")}>+ New drill</button>
        )}
      </div>

      {editing && options.data && (
        <DrillForm
          drill={editing === "new" ? null : editing}
          options={options.data}
          onSave={save}
          onCancel={() => setEditing(null)}
        />
      )}
      <ErrorMessage message={options.error} onRetry={options.reload} />

      <div className="filters card">
        <input
          type="search"
          placeholder="Search drills…"
          aria-label="Search drills"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select aria-label="Filter by category" value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {options.data?.categories.map((c) => <option key={c}>{c}</option>)}
        </select>
        <select aria-label="Filter by skill level" value={level} onChange={(e) => setLevel(e.target.value)}>
          <option value="">All levels</option>
          {options.data?.skill_levels.map((l) => <option key={l}>{l}</option>)}
        </select>
      </div>

      <ErrorMessage message={actionError} />
      {drills.loading && !drills.data && <Loading text="Loading drills…" />}
      <ErrorMessage message={drills.error} onRetry={drills.reload} />

      {drills.data && drills.data.drills.length === 0 && (
        <Empty title={filtersOn ? "No drills match those filters" : "No drills yet"}>
          <p className="muted">
            {filtersOn ? "Try clearing a filter." : "Create your first drill to get started."}
          </p>
        </Empty>
      )}

      {drills.data && (
        <ul className="grid">
          {drills.data.drills.map((drill) => (
            <li key={drill.id} className="card drill">
              <div className="tags">
                <span className={`tag ${categoryClass(drill.category)}`}>{drill.category}</span>
                <span className="tag level">{drill.skill_level}</span>
                <span className="tag time">{drill.default_minutes} min</span>
              </div>
              <h3>{drill.name}</h3>
              {drill.description && <p>{drill.description}</p>}
              {drill.equipment && <p className="muted">Equipment: {drill.equipment}</p>}
              <div className="actions">
                <button className="btn small" onClick={() => setEditing(drill)}>Edit</button>
                <ConfirmButton onConfirm={() => remove(drill)} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
