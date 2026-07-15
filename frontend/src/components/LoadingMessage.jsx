import { LoadingDots } from "./ui/Modal.jsx";

export function LoadingMessage({ message = "Загрузка..." }) {
  return (
    <div className="ui-loading-message" role="status" aria-live="polite">
      <LoadingDots className="ui-loading-message__dots" />
      <span className="ui-loading-message__text">{message}</span>
    </div>
  );
}
