import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";
import { LoadingMessage } from "./LoadingMessage.jsx";
import { StatusPage } from "./layout/StatusPage.jsx";

export function ProtectedRoute({ allowedRoles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <StatusPage>
        <LoadingMessage />
      </StatusPage>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={`/${user.role}`} replace />;
  }

  return <Outlet />;
}
