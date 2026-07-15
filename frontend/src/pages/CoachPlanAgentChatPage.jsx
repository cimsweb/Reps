import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import {
  confirmPlanAgentDraft,
  getActivePlanAgentSession,
  sendPlanAgentMessage,
  startPlanAgentSession,
} from "../api/client.js";
import { getToken } from "../auth/tokenStorage.js";
import { AgentChatLayout } from "../components/agent/AgentChatLayout.jsx";
import { PlanDraftPreview } from "../components/agent/AgentDraftPreview.jsx";
import { AiUnavailableBanner } from "../components/agent/AiUnavailableBanner.jsx";
import { LoadingMessage } from "../components/LoadingMessage.jsx";
import { getErrorMessage, isAiUnavailableError } from "../utils/apiErrors.js";
import { toDateInputValue } from "../utils/formatters.js";

const PLAN_TEMPLATES = [
  {
    label: "Беговая неделя",
    brief: "бег, отдых, бег, отдых, бег длинный, вело, бег лёгкий",
  },
  {
    label: "Смешанная",
    brief: "бег, зал, бег, отдых, бег, вело, бег",
  },
  {
    label: "Силовая",
    brief: "зал, отдых, зал, бег, зал, отдых, зал",
  },
];

export function CoachPlanAgentChatPage() {
  const { athleteId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState("");
  const [aiUnavailable, setAiUnavailable] = useState(false);
  const [showDraftPanel, setShowDraftPanel] = useState(true);
  const [startDate, setStartDate] = useState(toDateInputValue());
  const [brief, setBrief] = useState("");

  useEffect(() => {
    const queryBrief = searchParams.get("brief");
    const queryStartDate = searchParams.get("start_date");
    if (queryBrief) {
      setBrief(queryBrief);
    }
    if (queryStartDate) {
      setStartDate(queryStartDate);
    }
  }, [searchParams]);

  const loadActiveSession = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const activeSession = await getActivePlanAgentSession(token, athleteId);
      setSession(activeSession);
      if (activeSession?.can_confirm && activeSession.latest_reply?.type === "plan_draft") {
        setShowDraftPanel(true);
      }
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Не удалось загрузить сессию"));
    } finally {
      setLoading(false);
    }
  }, [athleteId]);

  useEffect(() => {
    loadActiveSession();
  }, [loadActiveSession]);

  async function handleStartSession(initialBrief) {
    setSending(true);
    setError("");
    setAiUnavailable(false);
    try {
      const token = getToken();
      const created = await startPlanAgentSession(token, athleteId, {
        start_date: startDate,
        initial_brief: initialBrief || undefined,
      });
      setSession(created);
      setShowDraftPanel(created.can_confirm && created.latest_reply?.type === "plan_draft");
    } catch (startError) {
      if (isAiUnavailableError(startError)) {
        setAiUnavailable(true);
      }
      setError(getErrorMessage(startError, "Не удалось начать диалог с ИИ"));
    } finally {
      setSending(false);
    }
  }

  async function handleSendMessage(content) {
    if (!session?.session_id) {
      return;
    }
    setSending(true);
    setError("");
    setAiUnavailable(false);
    try {
      const token = getToken();
      const updated = await sendPlanAgentMessage(token, session.session_id, { content });
      setSession(updated);
      if (updated.can_confirm && updated.latest_reply?.type === "plan_draft") {
        setShowDraftPanel(true);
      }
    } catch (sendError) {
      if (isAiUnavailableError(sendError)) {
        setAiUnavailable(true);
      }
      setError(getErrorMessage(sendError, "Не удалось отправить сообщение"));
    } finally {
      setSending(false);
    }
  }

  async function handleConfirmPlan() {
    if (!session?.session_id) {
      return;
    }
    setConfirming(true);
    setError("");
    try {
      const token = getToken();
      await confirmPlanAgentDraft(token, session.session_id, {});
      navigate(`/coach/athletes/${athleteId}`);
    } catch (confirmError) {
      setError(getErrorMessage(confirmError, "Не удалось сохранить план"));
    } finally {
      setConfirming(false);
    }
  }

  const planDraft =
    session?.can_confirm && session.latest_reply?.type === "plan_draft"
      ? session.latest_reply.draft
      : null;

  return (
    <div className="coach-page-content agent-chat-page">
      <p className="meta">
        <Link to={`/coach/athletes/${athleteId}`}>← Карточка спортсмена</Link>
      </p>
      <h1 className="coach-section-title">Создать план с ИИ</h1>

      {aiUnavailable ? (
        <AiUnavailableBanner
          fallbackHref={`/coach/athletes/${athleteId}`}
          fallbackLabel="Вернуться к спортсмену"
        />
      ) : null}
      {error ? <p className="form-error agent-chat-error">{error}</p> : null}

      {loading ? <LoadingMessage /> : null}

      {!loading && !session ? (
        <section className="agent-start-screen card">
          <p className="meta">
            Опишите неделю коротким брифом — агент задаст уточняющие вопросы и предложит черновик.
          </p>
          <label>
            Дата начала недели
            <input
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
            />
          </label>
          <div className="template-row">
            {PLAN_TEMPLATES.map((template) => (
              <button
                key={template.label}
                type="button"
                className="button-secondary"
                onClick={() => setBrief(template.brief)}
              >
                {template.label}
              </button>
            ))}
          </div>
          <label>
            Бриф (типы через запятую)
            <textarea
              rows={3}
              value={brief}
              placeholder="бег, зал, бег, отдых, бег, вело, бег"
              onChange={(event) => setBrief(event.target.value)}
            />
          </label>
          <div className="button-row">
            <button
              type="button"
              onClick={() => handleStartSession(brief.trim())}
              disabled={sending || !startDate}
            >
              {sending ? "Запускаем…" : "Начать диалог"}
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={() => navigate(`/coach/athletes/${athleteId}`)}
            >
              Отмена
            </button>
          </div>
        </section>
      ) : null}

      {!loading && session ? (
        <AgentChatLayout
          messages={session.messages}
          onSend={handleSendMessage}
          sending={sending}
          disabled={confirming}
          placeholder="Ответьте на вопрос агента…"
          footer={
            session.messages_remaining <= 3 ? (
              <p className="meta agent-chat-meta">
                Осталось сообщений: {session.messages_remaining}
              </p>
            ) : null
          }
        >
          {showDraftPanel && planDraft ? (
            <PlanDraftPreview
              draft={planDraft}
              confirming={confirming}
              onConfirm={handleConfirmPlan}
              onContinueEditing={() => setShowDraftPanel(false)}
              onCancel={() => navigate(`/coach/athletes/${athleteId}`)}
            />
          ) : null}
        </AgentChatLayout>
      ) : null}
    </div>
  );
}
