export function Card({ title, className = "", children }) {
  return (
    <section className={["ui-card", className].filter(Boolean).join(" ")}>
      {title ? <h2 className="ui-card__title">{title}</h2> : null}
      {children}
    </section>
  );
}
