const ROLE_OPTIONS = [
  { value: "athlete", label: "Я спортсмен" },
  { value: "coach", label: "Я тренер" },
];

export function AuthRoleSelector({ value, onChange }) {
  return (
    <div className="auth-role-segmented" role="tablist" aria-label="Роль">
      {ROLE_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          role="tab"
          aria-selected={value === option.value}
          className={[
            "auth-role-segmented__option",
            value === option.value ? "auth-role-segmented__option--active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
