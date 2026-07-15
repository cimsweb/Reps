export function SegmentedControl({ options, value, onChange, name, className = "" }) {
  return (
    <div className={["ui-segmented", className].filter(Boolean).join(" ")} role="tablist">
      {options.map((option) => {
        const isActive = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={isActive}
            name={name}
            className={["ui-segmented__option", isActive ? "ui-segmented__option--active" : ""]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
