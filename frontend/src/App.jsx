import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext.jsx";
import { ThemeProvider } from "./theme/ThemeProvider.jsx";
import { ProtectedRoute } from "./components/ProtectedRoute.jsx";
import { AdminDashboard } from "./pages/AdminDashboard.jsx";
import { AthleteLayout } from "./pages/athlete/AthleteLayout.jsx";
import { AthleteTodayPage } from "./pages/athlete/AthleteTodayPage.jsx";
import { AthleteWeekPage } from "./pages/athlete/AthleteWeekPage.jsx";
import { AthleteProgressPage } from "./pages/athlete/AthleteProgressPage.jsx";
import { AthleteChatPage } from "./pages/athlete/AthleteChatPage.jsx";
import { AthleteSettingsPage } from "./pages/athlete/AthleteSettingsPage.jsx";
import { CoachLayout } from "./pages/coach/CoachLayout.jsx";
import { CoachHomePage } from "./pages/coach/CoachHomePage.jsx";
import { CoachChatPage } from "./pages/coach/CoachChatPage.jsx";
import { CoachSettingsPage } from "./pages/coach/CoachSettingsPage.jsx";
import { CoachAthletePage } from "./pages/CoachAthletePage.jsx";
import { CoachPlanAgentChatPage } from "./pages/CoachPlanAgentChatPage.jsx";
import { AthleteReportAgentChatPage } from "./pages/AthleteReportAgentChatPage.jsx";
import { LoginPage } from "./pages/LoginPage.jsx";
import { RegisterPage } from "./pages/RegisterPage.jsx";
import "./styles/tokens.css";
import "./styles/base.css";
import "./components/ui/ui.css";
import "./components/layout/layout.css";
import "./components/auth/auth.css";
import "./components/athlete/athlete.css";
import "./components/coach/coach.css";
import "./components/chat/chat.css";
import "./components/training/feedbackForm.css";
import "./components/training/workoutText.css";
import "./components/training/weekNavigator.css";
import "./components/settings/settings.css";
import "./App.css";

function App() {
  return (
    <ThemeProvider>
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
            <Route element={<CoachLayout />}>
              <Route path="/coach" element={<CoachHomePage />} />
              <Route path="/coach/chat" element={<CoachChatPage />} />
              <Route path="/coach/settings" element={<CoachSettingsPage />} />
              <Route path="/coach/athletes/:athleteId" element={<CoachAthletePage />} />
              <Route
                path="/coach/athletes/:athleteId/training/ai"
                element={<CoachPlanAgentChatPage />}
              />
            </Route>
          </Route>
          <Route element={<ProtectedRoute allowedRoles={["athlete"]} />}>
            <Route
              path="/athlete/planned-workouts/:workoutId/report/ai"
              element={<AthleteReportAgentChatPage />}
            />
            <Route element={<AthleteLayout />}>
              <Route path="/athlete" element={<Navigate to="/athlete/today" replace />} />
              <Route path="/athlete/today" element={<AthleteTodayPage />} />
              <Route path="/athlete/week" element={<AthleteWeekPage />} />
              <Route path="/athlete/progress" element={<AthleteProgressPage />} />
              <Route path="/athlete/chat" element={<AthleteChatPage />} />
              <Route path="/athlete/settings" element={<AthleteSettingsPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
