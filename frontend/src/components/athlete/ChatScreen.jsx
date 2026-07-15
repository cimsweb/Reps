import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchAthleteCoaches,
  fetchAthleteConversationMessages,
  fetchAthleteConversations,
  markAthleteConversationRead,
  sendAthleteCoachMessage,
} from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";
import { Avatar } from "../ui/Avatar.jsx";
import { EmptyState } from "../EmptyState.jsx";
import { LoadingMessage } from "../LoadingMessage.jsx";
import { getErrorMessage } from "../../utils/apiErrors.js";
import { ChatComposer } from "../chat/ChatComposer.jsx";
import { ChatMessageList } from "../chat/ChatMessageList.jsx";
import {
  buildPartnerInitials,
  buildPartnerLabel,
} from "../chat/chatDisplay.js";

function useIsMobileView() {
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia("(max-width: 1023px)").matches : false,
  );

  useEffect(() => {
    const media = window.matchMedia("(max-width: 1023px)");
    function handleChange(event) {
      setIsMobile(event.matches);
    }
    media.addEventListener("change", handleChange);
    return () => media.removeEventListener("change", handleChange);
  }, []);

  return isMobile;
}

export function ChatScreen() {
  const [conversation, setConversation] = useState(null);
  const [coachLink, setCoachLink] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const isMobile = useIsMobileView();

  const loadChat = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const conversationsResult = await fetchAthleteConversations(token);
      const activeConversation = conversationsResult.items[0] ?? null;
      setConversation(activeConversation);

      if (!activeConversation) {
        const coachesResult = await fetchAthleteCoaches(token);
        setCoachLink(coachesResult.items[0] ?? null);
        setMessages([]);
        return;
      }

      setCoachLink(null);

      const messagesResult = await fetchAthleteConversationMessages(token, activeConversation.id, {
        limit: 100,
      });
      setMessages(messagesResult.items);
      await markAthleteConversationRead(token, activeConversation.id);
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Не удалось загрузить чат"));
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadChat();
  }, [loadChat]);

  async function handleSend(content) {
    const coachId = conversation?.partner_id ?? coachLink?.coach_id;
    if (!coachId) {
      return;
    }

    setSending(true);
    setError("");
    try {
      const token = getToken();
      const message = await sendAthleteCoachMessage(token, coachId, {
        content,
        kind: "text",
      });
      setMessages((current) => [...current, message]);
      setDraft("");
      if (!conversation) {
        await loadChat();
      }
    } catch (sendError) {
      setError(getErrorMessage(sendError, "Не удалось отправить сообщение"));
    } finally {
      setSending(false);
    }
  }

  const partner = useMemo(() => {
    if (conversation) {
      return conversation;
    }
    if (coachLink) {
      return { partner_email: "coach@reps.app", partner_id: coachLink.coach_id };
    }
    return null;
  }, [coachLink, conversation]);

  if (loading) {
    return <LoadingMessage />;
  }

  if (!partner) {
    return (
      <div className="athlete-shell-section athlete-chat-screen">
        <h2 className="athlete-tab-screen__title">Чат</h2>
        <EmptyState message="Пока нет переписки с тренером. Напишите первым, когда тренер будет подключён." />
        {error ? <p className="form-error">{error}</p> : null}
      </div>
    );
  }

  return (
    <div className="athlete-shell-section athlete-chat-screen">
      <header className="athlete-chat-header">
        <Avatar initials={buildPartnerInitials(partner.partner_email, "TR")} size="md" />
        <h2 className="athlete-chat-header__name">
          {buildPartnerLabel(partner.partner_email, "тренер")}
        </h2>
      </header>

      <ChatMessageList
        messages={messages}
        emptyMessage="Сообщений пока нет. Напишите тренеру."
      />

      {error ? <p className="form-error">{error}</p> : null}

      <ChatComposer
        value={draft}
        placeholder="Написать…"
        submitLabel={isMobile ? "➤" : "Отправить"}
        sending={sending}
        onChange={setDraft}
        onSubmit={handleSend}
      />
    </div>
  );
}
