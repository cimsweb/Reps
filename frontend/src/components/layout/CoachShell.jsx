import { COACH_NAV_ITEMS } from "../coach/coachTabs.js";
import { ThemeToggle } from "../ui/ThemeToggle.jsx";
import { Avatar } from "../ui/Avatar.jsx";

export function CoachShell({
  title = "Мои спортсмены",
  hideHeader = false,
  activeNav = "list",
  onNavChange,
  unreadCount = 0,
  userName = "Тренер",
  onLogout,
  footer,
  headerActions,
  children,
}) {
  function handleNavChange(navId) {
    onNavChange?.(navId);
  }

  return (
    <div className="layout-coach">
      <aside className="layout-coach-sidebar">
        <div className="layout-coach-sidebar__brand">
          <div className="layout-auth__logo">R</div>
          <div className="layout-auth__name layout-coach-sidebar__name">Reps</div>
          <ThemeToggle className="layout-shell-theme-toggle layout-shell-theme-toggle--sidebar" />
        </div>

        <nav className="layout-coach-nav" aria-label="Навигация тренера">
          {COACH_NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={[
                "layout-coach-nav__item",
                activeNav === item.id ? "layout-coach-nav__item--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => handleNavChange(item.id)}
            >
              <span className="layout-coach-nav__icon" aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
              {item.showUnread && unreadCount > 0 ? (
                <span className="layout-coach-nav__badge-count">{unreadCount}</span>
              ) : null}
            </button>
          ))}
        </nav>

        <div className="layout-coach-sidebar__footer">
          {footer ?? (
            <div className="layout-coach-sidebar__user">
              <Avatar initials={userName.slice(0, 2).toUpperCase()} size="md" />
              <div>
                <p className="layout-coach-sidebar__user-name">{userName}</p>
                <p className="layout-coach-sidebar__user-role">Тренер</p>
              </div>
            </div>
          )}
          {onLogout ? (
            <button type="button" className="layout-coach-sidebar__logout" onClick={onLogout}>
              Выйти
            </button>
          ) : null}
        </div>
      </aside>

      <div className="layout-coach-main">
        <div className="layout-mobile-topbar">
          <ThemeToggle className="layout-shell-theme-toggle layout-shell-theme-toggle--mobile" />
        </div>
        {!hideHeader ? (
          <header className="layout-coach-main__header">
            <div className="layout-coach-main__header-row">
              <div className="layout-coach-main__header-start">
                <h1 className="layout-coach-main__title">{title}</h1>
              </div>
              {headerActions}
            </div>
          </header>
        ) : null}
        {children}

        <nav className="layout-coach-bottom-tabs" aria-label="Навигация тренера">
          {COACH_NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={[
                "layout-coach-bottom-tabs__item",
                activeNav === item.id ? "layout-coach-bottom-tabs__item--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => handleNavChange(item.id)}
            >
              <span className="layout-coach-bottom-tabs__icon" aria-hidden="true">
                {item.icon}
              </span>
              <span className="layout-coach-bottom-tabs__label-full">{item.label}</span>
              <span className="layout-coach-bottom-tabs__label-short">{item.shortLabel ?? item.label}</span>
              {item.showUnread && unreadCount > 0 ? (
                <span className="layout-coach-bottom-tabs__dot" aria-label="Непрочитанные" />
              ) : null}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );
}
