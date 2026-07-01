import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext.jsx";
import { ProtectedRoute } from "./components/ProtectedRoute.jsx";
import { AdminDashboard } from "./pages/AdminDashboard.jsx";
import { AthleteDashboard } from "./pages/AthleteDashboard.jsx";
import { CoachDashboard } from "./pages/CoachDashboard.jsx";
import { LoginPage } from "./pages/LoginPage.jsx";
import { RegisterPage } from "./pages/RegisterPage.jsx";
import "./App.css";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
            <Route path="/admin" element={<AdminDashboard />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={["coach"]} />}>
            <Route path="/coach" element={<CoachDashboard />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={["athlete"]} />}>
            <Route path="/athlete" element={<AthleteDashboard />} />
          </Route>
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
