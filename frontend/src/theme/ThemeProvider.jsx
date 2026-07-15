import { createContext, useContext, useMemo, useState } from "react";

import { applyTheme, readStoredTheme, toggleStoredTheme } from "./themeStorage.js";

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => readStoredTheme());

  function toggleTheme() {
    setTheme((current) => toggleStoredTheme(current));
  }

  const value = useMemo(
    () => ({
      theme,
      isDark: theme === "dark",
      toggleTheme,
    }),
    [theme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}

export function initTheme() {
  applyTheme(readStoredTheme());
}
