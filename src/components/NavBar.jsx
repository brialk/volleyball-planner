import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="brand">
          <span aria-hidden="true">🏐</span> Rally Planner
        </NavLink>
        {user && (
          <nav className="nav-links" aria-label="Main">
            <NavLink to="/plans">Plans</NavLink>
            <NavLink to="/drills">Drills</NavLink>
            <span className="who">Hi, {user.username}</span>
            <button type="button" className="btn ghost small" onClick={handleLogout}>
              Log out
            </button>
          </nav>
        )}
      </div>
    </header>
  );
}
