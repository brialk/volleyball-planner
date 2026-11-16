import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { ErrorMessage, Loading } from "../components/StatusMessage.jsx";

// One form used for both /login and /signup.
export default function AuthPage({ mode }) {
  const isSignup = mode === "signup";
  const { user, checking, login, signup } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (checking) return <Loading text="Checking your login…" />;
  if (user) return <Navigate to="/plans" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await (isSignup ? signup : login)(username.trim(), password);
      navigate("/plans");
    } catch (problem) {
      setError(problem.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-card card">
      <h1>{isSignup ? "Create your account" : "Welcome back"}</h1>
      <p className="muted">
        {isSignup ? "Plan better practices in minutes." : "Log in to see your drills and practice plans."}
      </p>
      <form onSubmit={handleSubmit} className="form">
        <label>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={isSignup ? "new-password" : "current-password"}
            required
          />
        </label>
        {isSignup && <p className="hint">Username: 3–30 letters, numbers or _. Password: at least 8 characters.</p>}
        <ErrorMessage message={error} />
        <button className="btn primary" disabled={busy}>
          {busy ? "One moment…" : isSignup ? "Sign up" : "Log in"}
        </button>
      </form>
      <p className="muted center">
        {isSignup ? (
          <>Already have an account? <Link to="/login">Log in</Link></>
        ) : (
          <>New here? <Link to="/signup">Create an account</Link></>
        )}
      </p>
    </div>
  );
}
