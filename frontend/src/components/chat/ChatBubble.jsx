export function ChatBubble({ isMine, isQuestion, children }) {
  return (
    <div
      className={[
        "chat-bubble-wrap",
        isMine ? "chat-bubble-wrap--mine" : "chat-bubble-wrap--theirs",
      ].join(" ")}
    >
      <div
        className={["chat-bubble", isMine ? "chat-bubble--mine" : "chat-bubble--theirs"].join(" ")}
      >
        {isQuestion ? <p className="chat-bubble__question">❓ Вопрос</p> : null}
        {children}
      </div>
    </div>
  );
}
