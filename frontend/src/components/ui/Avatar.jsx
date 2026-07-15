const SIZE_CLASS = {
  sm: "ui-avatar--sm",
  md: "ui-avatar--md",
  lg: "ui-avatar--lg",
};

export function Avatar({ initials, size = "md", className = "", style }) {
  const classes = ["ui-avatar", SIZE_CLASS[size] ?? SIZE_CLASS.md, className]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={classes} style={style} aria-hidden="true">
      {initials}
    </span>
  );
}
