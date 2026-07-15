import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchCoachConversationMessages,
  fetchCoachConversations,
  markCoachConversationRead,
  sendCoachAthleteMessage,
} from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";
import { Avatar } from "../ui/Avatar.jsx";
import { EmptyState } from "../EmptyState.jsx";
import { LoadingMessage } from "../LoadingMessage.jsx";
import { getErrorMessage } from "../../utils/apiErrors.js";
import { ChatComposer } from "../chat/ChatComposer.jsx";
import { ChatMessageList } from "../chat/ChatMessageList.jsx";
import {
  buildAthleteListLabel,
  buildPartnerInitials,
  buildPartnerLabel,
} from "../chat/chatDisplay.js";

function useIsMobileChat() {
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

export function CoachChatScreen() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState("");
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const isMobile = useIsMobileChat();

  const loadConversations = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const result = await fetchCoachConversations(token);
      setConversations(result.items);
      const isMobileView = window.matchMedia("(max-width: 1023px)").matches;
      setActiveConversationId((current) => {
        if (current) {
          return current;
        }
        if (isMobileView) {
          return "";
        }
        return result.items[0]?.id || "";
      });
    } catch (loadError) {
      setConversations([]);
      setError(getErrorMessage(loadError, "Не удалось загрузить чаты"));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMessages = useCallback(async (conversationId) => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    setMessagesLoading(true);
    setError("");
    try {
      const token = getToken();
      const result = await fetchCoachConversationMessages(token, conversationId, { limit: 100 });
      setMessages(result.items);
      await markCoachConversationRead(token, conversationId);
      setConversations((current) =>
        current.map((item) =>
          item.id === conversationId ? { ...item, unread_count: 0 } : item,
        ),
      );
    } catch (loadError) {
      setMessages([]);
      setError(getErrorMessage(loadError, "Не удалось загрузить сообщения"));
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    loadMessages(activeConversationId);
  }, [activeConversationId, loadMessages]);

  const activeConversation = useMemo(
    () => conversations.find((item) => item.id === activeConversationId) ?? null,
    [activeConversationId, conversations],
  );

  async function handleSend(content) {
    if (!activeConversation) {
      return;
    }
    setSending(true);
    setError("");
    try {
      const token = getToken();
      const message = await sendCoachAthleteMessage(token, activeConversation.athlete_id, {
        content,
        kind: "text",
      });
      setMessages((current) => [...current, message]);
      setDraft("");
      await loadConversations();
    } catch (sendError) {
      setError(getErrorMessage(sendError, "Не удалось отправить сообщение"));
    } finally {
      setSending(false);
    }
  }

  function handleSelectConversation(conversationId) {
    setActiveConversationId(conversationId);
  }

  function handleBackToList() {
    setActiveConversationId("");
  }

  if (loading) {
    return <LoadingMessage />;
  }

  if (conversations.length === 0) {
    return (
      <div className="coach-chat-screen">
        <EmptyState message="Пока нет переписки со спортсменами. Напишите первым из карточки спортсмена." />
        {error ? <p className="form-error">{error}</p> : null}
      </div>
    );
  }

  const partnerEmail = activeConversation?.partner_email ?? "athlete@reps.app";
  const showMobileList = isMobile && !activeConversationId;
  const showMobileConversation = isMobile && Boolean(activeConversationId);

  const conversationList = (
    <aside className="chat-split__list">
      <h2 className="chat-split__list-title">Чат</h2>
      {conversations.map((conversation) => {
        const isActive = conversation.id === activeConversationId;
        return (
          <button
            key={conversation.id}
            type="button"
            className={[
              "chat-split__list-item",
              isActive ? "chat-split__list-item--active" : "",
              conversation.unread_count > 0 ? "chat-split__list-item--unread" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => handleSelectConversation(conversation.id)}
          >
            <Avatar
              initials={buildPartnerInitials(conversation.partner_email, "AT")}
              size="sm"
            />
            <div className="chat-split__list-row">
              <div className="chat-split__list-text">
                <p className="chat-split__list-name">{buildAthleteListLabel(conversation)}</p>
                <p className="chat-split__list-preview">
                  {conversation.last_message_content || "Нет сообщений"}
                </p>
              </div>
              {conversation.unread_count > 0 ? (
                <span className="chat-split__unread" aria-label="Непрочитанные" />
              ) : null}
            </div>
          </button>
        );
      })}
    </aside>
  );

  const conversationPanel = activeConversation ? (
    <section className="chat-split__conversation">
      <header className="chat-split__conversation-header">
        {isMobile ? (
          <button
            type="button"
            className="chat-split__back"
            onClick={handleBackToList}
            aria-label="Назад к списку чатов"
          >
            ←
          </button>
        ) : null}
        <Avatar initials={buildPartnerInitials(partnerEmail, "AT")} size="md" />
        <h3 className="chat-split__conversation-name">
          {buildPartnerLabel(partnerEmail, "спортсмен")}
        </h3>
      </header>

      <div className="chat-panel__messages">
        {messagesLoading ? <LoadingMessage /> : null}
        {!messagesLoading ? (
          <ChatMessageList
            messages={messages}
            emptyMessage="Сообщений пока нет. Напишите спортсмену."
          />
        ) : null}
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      <ChatComposer
        value={draft}
        placeholder={isMobile ? "Написать…" : "Написать сообщение…"}
        submitLabel={isMobile ? "➤" : "Отправить"}
        sending={sending}
        onChange={setDraft}
        onSubmit={handleSend}
      />
    </section>
  ) : null;

  if (showMobileList) {
    return <div className="coach-chat-screen coach-chat-screen--mobile-list">{conversationList}</div>;
  }

  if (showMobileConversation) {
    return (
      <div className="coach-chat-screen coach-chat-screen--mobile-conversation">
        {conversationPanel}
      </div>
    );
  }

  return (
    <div className="coach-chat-screen">
      <div className="chat-split">
        {conversationList}
        {conversationPanel}
      </div>
    </div>
  );
}
