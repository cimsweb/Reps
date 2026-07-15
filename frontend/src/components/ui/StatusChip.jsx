const STATUS_LABELS = {
  done: "Выполнено",
  today: "Сегодня",
  soon: "Скоро",
  missed: "Пропущено",
  pending: "Ожидает",
};

const VARIANT_CLASS = {
  done: "ui-status-chip--done",
  today: "ui-status-chip--today",
  soon: "ui-status-chip--soon",
  missed: "ui-status-chip--missed",
  pending: "ui-status-chip--pending",
};

export function StatusChip({ variant = "pending", label, className = "" }) {
  const classes = ["ui-status-chip", VARIANT_CLASS[variant] ?? VARIANT_CLASS.pending, className]
    .filter(Boolean)
    .join(" ");

  return <span className={classes}>{label ?? STATUS_LABELS[variant] ?? variant}</span>;
}
