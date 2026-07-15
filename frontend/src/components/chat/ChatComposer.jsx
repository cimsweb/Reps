import { Button } from "../ui/Button.jsx";

export function ChatComposer({
  value,
  placeholder = "Написать…",
  sending = false,
  disabled = false,
  submitLabel = "Отправить",
  onChange,
  onSubmit,
}) {
  function handleSubmit(event) {
    event.preventDefault();
    if (!value.trim() || sending || disabled) {
      return;
    }
    onSubmit?.(value.trim());
  }

  return (
    <form className="chat-composer" onSubmit={handleSubmit}>
      <input
        className="chat-composer__input"
        value={value}
        placeholder={placeholder}
        disabled={disabled || sending}
        onChange={(event) => onChange(event.target.value)}
      />
      <Button type="submit" variant="primaryDark" disabled={disabled || sending || !value.trim()}>
        {sending ? "…" : submitLabel}
      </Button>
    </form>
  );
}
