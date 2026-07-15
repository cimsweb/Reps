export function AuthErrorBanner({ message }) {
  if (!message) {
    return null;
  }

  return (
    <p className="auth-error-banner" role="alert">
      {message}
    </p>
  );
}
