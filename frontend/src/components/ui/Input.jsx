import { Label } from "./Label.jsx";

export function Input({ id, label, error, className = "", uppercaseLabel = true, ...props }) {
  const inputId = id ?? (label ? `input-${label.replace(/\s+/g, "-").toLowerCase()}` : undefined);
  const inputClass = ["ui-input", error ? "ui-input--error" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="ui-field">
      {label ? (
        <Label htmlFor={inputId} uppercase={uppercaseLabel}>
          {label}
        </Label>
      ) : null}
      <input id={inputId} className={inputClass} {...props} />
      {error ? <p className="ui-field-error">{error}</p> : null}
    </div>
  );
}
