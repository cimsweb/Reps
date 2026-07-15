import { Label } from "./Label.jsx";

export function Textarea({ id, label, error, className = "", uppercaseLabel = true, ...props }) {
  const textareaId =
    id ?? (label ? `textarea-${label.replace(/\s+/g, "-").toLowerCase()}` : undefined);
  const textareaClass = ["ui-textarea", error ? "ui-textarea--error" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="ui-field">
      {label ? (
        <Label htmlFor={textareaId} uppercase={uppercaseLabel}>
          {label}
        </Label>
      ) : null}
      <textarea id={textareaId} className={textareaClass} {...props} />
      {error ? <p className="ui-field-error">{error}</p> : null}
    </div>
  );
}
