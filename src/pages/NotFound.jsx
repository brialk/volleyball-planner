import { Link } from "react-router-dom";
import { Empty } from "../components/StatusMessage.jsx";

export default function NotFound() {
  return (
    <Empty title="Out of bounds!">
      <p className="muted">That page does not exist.</p>
      <Link className="btn primary" to="/plans">Back to my plans</Link>
    </Empty>
  );
}
