import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { Loading } from "./StatusMessage.jsx";

// Wraps every page that needs a login.
export default function ProtectedRoute() {
  const { user, checking } = useAuth();
  if (checking) return <Loading text="Checking your login…" />;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}
