import { useTheme } from "../../theme/ThemeProvider.jsx";

export function ThemeToggle({ className = "" }) {
  const { theme, toggleTheme } = useTheme();
  const icon = theme === "dark" ? "☀️" : "🌙";

  return (
    <button
      type="button"
      className={["theme-toggle", className].filter(Boolean).join(" ")}
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "Включить светлую тему" : "Включить тёмную тему"}
    >
      <span aria-hidden="true">{icon}</span>
    </button>
  );
}
