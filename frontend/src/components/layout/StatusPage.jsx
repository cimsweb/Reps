export function StatusPage({ wide = false, children }) {
  const innerClass = ["layout-status-page__inner", wide ? "layout-status-page__inner--wide" : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <main className="layout-status-page">
      <div className={innerClass}>{children}</div>
    </main>
  );
}
