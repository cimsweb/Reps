export function DashboardLayout({ title, subtitle, onLogout, children, wide = true }) {
  return (
    <main className="page">
      <section className={wide ? "card wide" : "card"}>
        <header className="dashboard-header">
          <div>
            <h1>{title}</h1>
            {subtitle ? <p>{subtitle}</p> : null}
          </div>
          <button type="button" onClick={onLogout}>
            Выйти
          </button>
        </header>
        {children}
      </section>
    </main>
  );
}
