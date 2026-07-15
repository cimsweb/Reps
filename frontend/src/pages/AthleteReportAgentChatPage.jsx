import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  confirmReportAgentDraft,
  fetchAthleteTrainingPlan,
  getActiveReportAgentSession,
  sendReportAgentMessage,
  startReportAgentSession,
  submitWorkoutReport,
} from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { getToken } from "../auth/tokenStorage.js";
import { AgentChatLayout } from "../components/agent/AgentChatLayout.jsx";
import { ReportDraftPreview } from "../components/agent/AgentDraftPreview.jsx";
import { AiUnavailableBanner } from "../components/agent/AiUnavailableBanner.jsx";
import { WorkoutReportForm } from "../components/training/WorkoutReportForm.jsx";
import { LoadingMessage } from "../components/LoadingMessage.jsx";
import { formatDate, formatWorkoutType, toDateInputValue } from "../utils/formatters.js";
import { getErrorMessage, isAiUnavailableError } from "../utils/apiErrors.js";

export function AthleteReportAgentChatPage() {
  const { workoutId } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [workout, setWorkout] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState("");
  const [aiUnavailable, setAiUnavailable] = useState(false);
  const [manualMode, setManualMode] = useState(false);
  const [manualSubmitting, setManualSubmitting] = useState(false);

  const loadPage = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const [planResult, activeSession] = await Promise.all([
        fetchAthleteTrainingPlan(token, {
          period: "week",
          anchorDate: toDateInputValue(),
        }),
        getActiveReportAgentSession(token, workoutId),
      ]);
      const matchedWorkout = planResult.workouts.find((item) => item.id === workoutId);
      if (!matchedWorkout) {
        setError("Тренировка не найдена в текущем плане.");
        setWorkout(null);
        setSession(null);
        return;
      }
      setWorkout(matchedWorkout);
      if (activeSession) {
        setSession(activeSession);
      }
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Не удалось загрузить данные"));
    } finally {
      setLoading(false);
    }
  }, [workoutId]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  async function ensureSession() {
    if (session?.session_id) {
      return session;
    }
    setSending(true);
    setError("");
    setAiUnavailable(false);
    try {
      const token = getToken();
      const created = await startReportAgentSession(token, workoutId);
      setSession(created);
      return created;
    } catch (startError) {
      if (isAiUnavailableError(startError)) {
        setAiUnavailable(true);
        setManualMode(true);
      }
      setError(getErrorMessage(startError, "Не удалось начать диалог с ИИ"));
      return null;
    } finally {
      setSending(false);
    }
  }

  async function handleSendMessage(content) {
    const currentSession = session || (await ensureSession());
    if (!currentSession?.session_id) {
      return;
    }
    setSending(true);
    setError("");
    setAiUnavailable(false);
    try {
      const token = getToken();
      const updated = await sendReportAgentMessage(token, currentSession.session_id, { content });
      setSession(updated);
    } catch (sendError) {
      if (isAiUnavailableError(sendError)) {
        setAiUnavailable(true);
        setManualMode(true);
      }
      setError(getErrorMessage(sendError, "Не удалось отправить сообщение"));
    } finally {
      setSending(false);
    }
  }

  async function handleConfirmReport(payload) {
    if (!session?.session_id) {
      return;
    }
    setConfirming(true);
    setError("");
    try {
      const token = getToken();
      await confirmReportAgentDraft(token, session.session_id, payload);
      navigate("/athlete/today");
    } catch (confirmError) {
      setError(getErrorMessage(confirmError, "Не удалось отправить отчёт"));
    } finally {
      setConfirming(false);
    }
  }

  async function handleManualSubmit(payload) {
    setManualSubmitting(true);
    setError("");
    try {
      const token = getToken();
      await submitWorkoutReport(token, workoutId, payload);
      navigate("/athlete/today");
    } catch (submitError) {
      setError(getErrorMessage(submitError, "Не удалось отправить отчёт"));
    } finally {
      setManualSubmitting(false);
    }
  }

  const reportDraft =
    session?.can_confirm && session.latest_reply?.type === "report_draft"
      ? session.latest_reply
      : null;

  const workoutContext = workout ? (
    <div className="agent-workout-context">
      <strong>{workout.title || formatWorkoutType(workout.workout_type)}</strong>
      <p className="meta">
        {formatDate(workout.planned_date)} · {formatWorkoutType(workout.workout_type)}
      </p>
      {workout.cycles?.length ? (
        <ul className="agent-workout-context-list">
          {workout.cycles.flatMap((cycle) =>
            cycle.exercises.map((exercise) => (
              <li key={exercise.id}>
                {exercise.name}
                {exercise.details ? ` — ${exercise.details}` : ""}
              </li>
            )),
          )}
        </ul>
      ) : null}
    </div>
  ) : null;

  return (
    <main className="page agent-chat-page">
      <header className="agent-chat-header">
        <div>
          <h1>Помощник отчёта</h1>
          <p className="meta">
            {user.email} · <Link to="/athlete/today">← Кабинет</Link>
          </p>
        </div>
        <button type="button" onClick={logout}>
          Выйти
        </button>
      </header>

      {aiUnavailable ? (
        <AiUnavailableBanner message="ИИ недоступен. Заполните отчёт вручную." />
      ) : null}
      {error ? <p className="form-error agent-chat-error">{error}</p> : null}

      {loading ? <LoadingMessage /> : null}

      {!loading && workout && manualMode ? (
        <section className="card">
          <WorkoutReportForm
            workout={workout}
            submitting={manualSubmitting}
            error={manualSubmitting ? "" : error}
            onSubmit={handleManualSubmit}
          />
          {!aiUnavailable ? (
            <button type="button" className="button-secondary" onClick={() => setManualMode(false)}>
              Вернуться к чату с ИИ
            </button>
          ) : null}
        </section>
      ) : null}

      {!loading && workout && !manualMode ? (
        <AgentChatLayout
          messages={session?.messages || []}
          onSend={handleSendMessage}
          sending={sending}
          disabled={confirming}
          placeholder="Например: нагрузка 5, тяжело на интервалах…"
          header={workoutContext}
          footer={
            !session ? (
              <p className="meta agent-chat-meta">
                Напишите первое сообщение — агент начнёт задавать вопросы.
              </p>
            ) : null
          }
        >
          {reportDraft ? (
            <ReportDraftPreview
              draft={reportDraft}
              confirming={confirming}
              onConfirm={handleConfirmReport}
              onManualFallback={() => setManualMode(true)}
            />
          ) : null}
        </AgentChatLayout>
      ) : null}
    </main>
  );
}
