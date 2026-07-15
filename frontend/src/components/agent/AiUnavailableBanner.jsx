import { Link } from "react-router-dom";

export function AiUnavailableBanner({ message, fallbackHref, fallbackLabel }) {
  return (
    <div className="ai-unavailable-banner" role="alert">
      <p>{message || "ИИ недоступен. Попробуйте позже или используйте ручной ввод."}</p>
      {fallbackHref ? (
        <Link to={fallbackHref} className="button-secondary section-link">
          {fallbackLabel || "Ручной ввод"}
        </Link>
      ) : null}
    </div>
  );
}
