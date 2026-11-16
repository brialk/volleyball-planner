import { useState } from "react";

// A delete button that asks "Sure?" first, so nothing is deleted by accident.
export default function ConfirmButton({ label = "Delete", onConfirm, disabled }) {
  const [asking, setAsking] = useState(false);

  if (!asking) {
    return (
      <button type="button" className="btn danger-ghost small" onClick={() => setAsking(true)} disabled={disabled}>
        {label}
      </button>
    );
  }
  return (
    <span className="confirm">
      <span>Sure?</span>
      <button
        type="button"
        className="btn danger small"
        onClick={() => { setAsking(false); onConfirm(); }}
      >
        Yes, {label.toLowerCase()}
      </button>
      <button type="button" className="btn ghost small" onClick={() => setAsking(false)}>
        No
      </button>
    </span>
  );
}
