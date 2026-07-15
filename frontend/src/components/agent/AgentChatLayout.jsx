import { useEffect, useRef, useState } from "react";

import { ChatBubble } from "../chat/ChatBubble.jsx";
import { Button } from "../ui/Button.jsx";

export function AgentChatLayout({
  messages,
  onSend,
  sending,
  disabled = false,
  placeholder = "Напишите сообщение…",
  header,
  footer,
  children,
}) {
  const [draft, setDraft] = useState("");
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, sending, children]);

  function handleSubmit(event) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || sending || disabled) {
      return;
    }
    setDraft("");
    onSend(content);
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  }

  return (
    <div className="agent-chat-layout">
      {header ? <div className="agent-chat-context">{header}</div> : null}
      <div className="agent-chat-messages chat-message-list" ref={listRef}>
        {messages.map((message) => (
          <ChatBubble key={message.sort_order} isMine={message.role === "user"}>
            <p>{message.content}</p>
          </ChatBubble>
        ))}
        {sending ? (
          <ChatBubble isMine={false}>
            <span className="ui-loading-dots" aria-label="ИИ печатает">
              <span className="ui-loading-dots__dot" />
              <span className="ui-loading-dots__dot" />
              <span className="ui-loading-dots__dot" />
            </span>
          </ChatBubble>
        ) : null}
        {children}
      </div>
      {footer}
      <form className="chat-composer agent-chat-input" onSubmit={handleSubmit}>
        <textarea
          className="chat-composer__input"
          rows={2}
          value={draft}
          placeholder={placeholder}
          disabled={disabled || sending}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
        />
        <Button type="submit" variant="primaryDark" disabled={disabled || sending || !draft.trim()}>
          {sending ? "…" : "Отправить"}
        </Button>
      </form>
    </div>
  );
}
