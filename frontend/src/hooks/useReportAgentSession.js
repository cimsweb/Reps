import { useCallback, useState } from "react";

import {
  getActiveReportAgentSession,
  sendReportAgentMessage,
  startReportAgentSession,
} from "../api/client.js";
import { getToken } from "../auth/tokenStorage.js";
import { getErrorMessage, isAiUnavailableError } from "../utils/apiErrors.js";

export function useReportAgentSession(workoutId) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const generatePolishedReport = useCallback(
    async (rawComment) => {
      if (!workoutId) {
        return null;
      }
      setGenerating(true);
      setError("");
      try {
        const token = getToken();
        let session = await getActiveReportAgentSession(token, workoutId);
        if (!session?.session_id) {
          session = await startReportAgentSession(token, workoutId);
        }
        const prompt =
          rawComment.trim() ||
          "Составь развёрнутый отчёт о тренировке для тренера на основе краткого комментария спортсмена.";
        const updated = await sendReportAgentMessage(token, session.session_id, {
          content: prompt,
        });
        const draft =
          updated.latest_reply?.type === "report_draft" ? updated.latest_reply : null;
        return draft?.comment_body?.trim() || null;
      } catch (generateError) {
        if (isAiUnavailableError(generateError)) {
          setError("ИИ сейчас недоступен. Заполните отчёт вручную.");
        } else {
          setError(getErrorMessage(generateError, "Не удалось составить отчёт с ИИ"));
        }
        return null;
      } finally {
        setGenerating(false);
      }
    },
    [workoutId],
  );

  return { generatePolishedReport, generating, error };
}
