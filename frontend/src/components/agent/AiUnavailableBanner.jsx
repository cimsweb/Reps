import { Link } from "react-router-dom";

function formatRequestBody(requestBody) {
  if (requestBody == null) {
    return "";
  }
  if (typeof requestBody === "string") {
    return requestBody;
  }
  try {
    return JSON.stringify(requestBody, null, 2);
  } catch {
    return String(requestBody);
  }
}

export function AiUnavailableBanner({ message, fallbackHref, fallbackLabel, details }) {
  const hasDetails =
    details &&
    (details.message || details.requestPath || details.requestBody != null);

  return (
    <div className="ai-unavailable-banner" role="alert">
      <p>{message || "ИИ недоступен. Попробуйте позже или используйте ручной ввод."}</p>
      {hasDetails ? (
        <div className="ai-unavailable-banner__bubble">
          {details.message ? (
            <p className="ai-unavailable-banner__bubble-line">
              <span className="ai-unavailable-banner__bubble-label">Ошибка</span>
              {details.message}
            </p>
          ) : null}
          {details.requestPath ? (
            <p className="ai-unavailable-banner__bubble-line">
              <span className="ai-unavailable-banner__bubble-label">Запрос</span>
              <code>{details.requestPath}</code>
            </p>
          ) : null}
          {details.requestBody != null ? (
            <pre className="ai-unavailable-banner__bubble-body">{formatRequestBody(details.requestBody)}</pre>
          ) : null}
        </div>
      ) : null}
      {fallbackHref ? (
        <Link to={fallbackHref} className="button-secondary section-link">
          {fallbackLabel || "Ручной ввод"}
        </Link>
      ) : null}
    </div>
  );
}
