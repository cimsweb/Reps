const VARIANT_CLASS = {
  primary: "ui-btn--primary",
  primaryDark: "ui-btn--primary-dark",
  outline: "ui-btn--outline",
  ghost: "ui-btn--ghost",
};

export function Button({
  variant = "primary",
  type = "button",
  block = false,
  loading = false,
  disabled = false,
  className = "",
  children,
  ...props
}) {
  const classes = [
    "ui-btn",
    VARIANT_CLASS[variant] ?? VARIANT_CLASS.primary,
    block ? "ui-btn--block" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button type={type} className={classes} disabled={disabled || loading} {...props}>
      {loading ? (
        <>
          <span className="ui-loading-dots" aria-hidden="true">
            <span className="ui-loading-dots__dot" />
            <span className="ui-loading-dots__dot" />
            <span className="ui-loading-dots__dot" />
          </span>
          <span className="sr-only">{children}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
