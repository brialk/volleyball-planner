import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { useLoad } from "../hooks.js";
import { formatDate } from "../utils.js";
import PlanForm from "../components/PlanForm.jsx";
import TimeBar from "../components/TimeBar.jsx";
import { Empty, ErrorMessage, Loading } from "../components/StatusMessage.jsx";

export default function PlansPage() {
  const plans = useLoad(() => api.getPlans(), []);
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  async function create(values) {
    const data = await api.createPlan(values);
    navigate(`/plans/${data.plan.id}`); // jump straight in to add drills
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Practice plans</h1>
          <p className="muted">Build a plan from your drills and keep it on time.</p>
        </div>
        {!creating && <button className="btn primary" onClick={() => setCreating(true)}>+ New plan</button>}
      </div>

      {creating && <PlanForm onSave={create} onCancel={() => setCreating(false)} />}

      {plans.loading && !plans.data && <Loading text="Loading plans…" />}
      <ErrorMessage message={plans.error} onRetry={plans.reload} />

      {plans.data && plans.data.plans.length === 0 && (
        <Empty title="No practice plans yet">
          <p className="muted">Create a plan, then add drills to it.</p>
        </Empty>
      )}

      {plans.data && (
        <ul className="grid">
          {plans.data.plans.map((plan) => (
            <li key={plan.id} className="card plan">
              <p className="muted small-text">{formatDate(plan.practice_date)}</p>
              <h3><Link to={`/plans/${plan.id}`}>{plan.title}</Link></h3>
              {plan.focus && <p>{plan.focus}</p>}
              <p className="muted">{plan.item_count} {plan.item_count === 1 ? "drill" : "drills"}</p>
              <TimeBar total={plan.total_minutes} target={plan.target_minutes} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
