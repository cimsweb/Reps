import { useEffect } from "react";

export function LoadingDots({ className = "" }) {
  return (
    <span className={["ui-loading-dots", className].filter(Boolean).join(" ")} aria-hidden="true">
      <span className="ui-loading-dots__dot" />
      <span className="ui-loading-dots__dot" />
      <span className="ui-loading-dots__dot" />
    </span>
  );
}

export function Modal({ open, onClose, title, wide = false, children }) {
  useEffect(() => {
    if (!open) {
      return undefined;
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  const modalClass = ["ui-modal", wide ? "ui-modal--wide" : ""].filter(Boolean).join(" ");

  return (
    <div className="ui-modal-overlay" role="presentation" onClick={onClose}>
      <div
        className={modalClass}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "ui-modal-title" : undefined}
        onClick={(event) => event.stopPropagation()}
      >
        {title ? (
          <header className="ui-modal__header">
            <h2 id="ui-modal-title" className="ui-modal__title">
              {title}
            </h2>
            <button
              type="button"
              className="ui-modal__close"
              onClick={onClose}
              aria-label="Закрыть"
            >
              ✕
            </button>
          </header>
        ) : null}
        {children}
      </div>
    </div>
  );
}
