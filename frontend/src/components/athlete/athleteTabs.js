/** Athlete bottom tab definitions and route helpers. */

export const ATHLETE_TABS = [
  { id: "today", path: "/athlete/today", label: "Сегодня", icon: "🏃" },
  { id: "week", path: "/athlete/week", label: "Неделя", icon: "📅" },
  { id: "progress", path: "/athlete/progress", label: "Прогресс", icon: "📈" },
  { id: "chat", path: "/athlete/chat", label: "Чат", icon: "💬" },
  { id: "settings", path: "/athlete/settings", label: "Настройки ИИ", shortLabel: "Настройки", icon: "⚙️" },
];

export function resolveAthleteTabId(pathname) {
  const match = ATHLETE_TABS.find(
    (tab) => pathname === tab.path || pathname.startsWith(`${tab.path}/`),
  );
  return match?.id ?? "today";
}

export function resolveAthleteTabPath(tabId) {
  return ATHLETE_TABS.find((tab) => tab.id === tabId)?.path ?? "/athlete/today";
}
