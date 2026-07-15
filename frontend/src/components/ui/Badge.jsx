const VARIANT_CLASS = {
  neutral: "ui-badge--neutral",
  success: "ui-badge--success",
  warning: "ui-badge--warning",
  danger: "ui-badge--danger",
};

export function Badge({ variant = "neutral", className = "", children }) {
  const classes = ["ui-badge", VARIANT_CLASS[variant] ?? VARIANT_CLASS.neutral, className]
    .filter(Boolean)
    .join(" ");

  return <span className={classes}>{children}</span>;
}
