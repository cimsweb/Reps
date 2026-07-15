export function ErrorBanner({ message, className = "" }) {
  if (!message) {
    return null;
  }

  return (
    <p className={["ui-error-banner", className].filter(Boolean).join(" ")} role="alert">
      {message}
    </p>
  );
}
