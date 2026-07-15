export function Label({ htmlFor, uppercase = true, className = "", children }) {
  const classes = ["ui-label", uppercase ? "" : "ui-label--default", className]
    .filter(Boolean)
    .join(" ");

  return (
    <label htmlFor={htmlFor} className={classes}>
      {children}
    </label>
  );
}
