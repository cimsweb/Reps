const THEME_STORAGE_KEY = "reps_theme";

export function readStoredTheme() {
  if (typeof window === "undefined") {
    return "light";
  }
  return localStorage.getItem(THEME_STORAGE_KEY) === "dark" ? "dark" : "light";
}

export function saveStoredTheme(theme) {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
}

export function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
}

export function toggleStoredTheme(currentTheme) {
  const nextTheme = currentTheme === "dark" ? "light" : "dark";
  saveStoredTheme(nextTheme);
  applyTheme(nextTheme);
  return nextTheme;
}
