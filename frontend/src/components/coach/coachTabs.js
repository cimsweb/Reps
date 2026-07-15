/** Coach sidebar navigation and route helpers. */

export const COACH_NAV_ITEMS = [
  { id: "list", path: "/coach", label: "Спортсмены", icon: "🏃" },
  { id: "chat", path: "/coach/chat", label: "Чат", icon: "💬", showUnread: true },
  {
    id: "settings",
    path: "/coach/settings",
    label: "Настройки ИИ",
    shortLabel: "Настройки",
    icon: "⚙️",
  },
];

export function resolveCoachNavId(pathname) {
  if (pathname.startsWith("/coach/chat")) {
    return "chat";
  }
  if (pathname.startsWith("/coach/settings")) {
    return "settings";
  }
  return "list";
}

export function resolveCoachNavPath(navId) {
  return COACH_NAV_ITEMS.find((item) => item.id === navId)?.path ?? "/coach";
}

export function resolveCoachPageTitle(pathname) {
  if (pathname.startsWith("/coach/chat")) {
    return "Чат";
  }
  if (pathname.startsWith("/coach/settings")) {
    return "Настройки ИИ";
  }
  if (pathname.startsWith("/coach/athletes/")) {
    return "Карточка спортсмена";
  }
  return "Спортсмены";
}

export function isCoachListRoute(pathname) {
  return pathname === "/coach" || pathname === "/coach/";
}

export function isCoachCustomHeaderRoute(pathname) {
  if (isCoachListRoute(pathname)) {
    return true;
  }
  if (pathname.startsWith("/coach/settings")) {
    return true;
  }
  const isAthleteDetail =
    pathname.startsWith("/coach/athletes/") && !pathname.includes("/training/");
  return isAthleteDetail;
}
