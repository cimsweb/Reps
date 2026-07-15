import { ChatBubble } from "./ChatBubble.jsx";

export function ChatMessageList({ messages, emptyMessage = "Сообщений пока нет." }) {
  if (messages.length === 0) {
    return <p className="chat-empty">{emptyMessage}</p>;
  }

  return (
    <div className="chat-message-list" aria-live="polite">
      {messages.map((message) => {
        const isMine = message.is_mine ?? message.role === "user";
        const isQuestion = message.kind === "question" && !isMine;
        const content = message.content ?? message.text;

        return (
          <ChatBubble key={message.id ?? message.sort_order} isMine={isMine} isQuestion={isQuestion}>
            <p>{content}</p>
          </ChatBubble>
        );
      })}
    </div>
  );
}
