export function EmptyState({ message, icon = "📭", children }) {
  return (
    <div className="ui-empty-state" role="status">
      {icon ? (
        <span className="ui-empty-state__icon" aria-hidden="true">
          {icon}
        </span>
      ) : null}
      <p className="ui-empty-state__message">{message}</p>
      {children ? <div className="ui-empty-state__actions">{children}</div> : null}
    </div>
  );
}
