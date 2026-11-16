import { timeBalance } from "../utils.js";

// Shows planned minutes against the target as a progress bar.
export default function TimeBar({ total, target }) {
  const percent = Math.min(100, Math.round((total / target) * 100));
  const balance = timeBalance(total, target);
  return (
    <div className="timebar">
      <div className="timebar-text">
        <span><strong>{total}</strong> of {target} min planned</span>
        <span className={`balance ${balance.tone}`}>{balance.text}</span>
      </div>
      <div
        className="track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={target}
        aria-valuenow={Math.min(total, target)}
        aria-label="Planned time"
      >
        <div className={`fill ${balance.tone}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
