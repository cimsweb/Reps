import { ATHLETE_TABS } from "../athlete/athleteTabs.js";
import { ThemeToggle } from "../ui/ThemeToggle.jsx";
import { Avatar } from "../ui/Avatar.jsx";

export function AthleteShell({
  userName = "Спортсмен",
  userSubtitle = "",
  activeTab = "today",
  onTabChange,
  hasUnreadChat = false,
  onLogout,
  children,
}) {
  return (
    <div className="layout-athlete">
      <aside className="layout-athlete-sidebar" aria-label="Навигация спортсмена">
        <div className="layout-athlete-sidebar__brand">
          <div className="layout-auth__logo">R</div>
          <div className="layout-auth__name layout-athlete-sidebar__name">Reps</div>
          <ThemeToggle className="layout-shell-theme-toggle layout-shell-theme-toggle--sidebar" />
        </div>

        <nav className="layout-athlete-sidebar__nav">
          {ATHLETE_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={[
                "layout-athlete-sidebar__nav-item",
                activeTab === tab.id ? "layout-athlete-sidebar__nav-item--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onTabChange?.(tab.id)}
            >
              <span className="layout-athlete-sidebar__nav-icon" aria-hidden="true">
                {tab.icon}
              </span>
              {tab.label}
              {tab.id === "chat" && hasUnreadChat ? (
                <span className="layout-athlete-sidebar__nav-dot" aria-label="Непрочитанные" />
              ) : null}
            </button>
          ))}
        </nav>

        <div className="layout-athlete-sidebar__footer">
          <div className="layout-athlete-sidebar__user">
            <Avatar initials={userName.slice(0, 2).toUpperCase()} size="md" />
            <div>
              <p className="layout-athlete-sidebar__user-name">{userName}</p>
              {userSubtitle ? (
                <p className="layout-athlete-sidebar__user-subtitle">{userSubtitle}</p>
              ) : null}
            </div>
          </div>
          {onLogout ? (
            <button type="button" className="layout-athlete-sidebar__logout" onClick={onLogout}>
              Выйти
            </button>
          ) : null}
        </div>
      </aside>

      <div className="layout-athlete-body">
        <div className="layout-mobile-topbar">
          <ThemeToggle className="layout-shell-theme-toggle layout-shell-theme-toggle--mobile" />
        </div>
        <main className="layout-athlete-main">{children}</main>

        <nav className="layout-athlete-tabs" aria-label="Навигация спортсмена">
          {ATHLETE_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={[
                "layout-athlete-tabs__item",
                activeTab === tab.id ? "layout-athlete-tabs__item--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onTabChange?.(tab.id)}
            >
              <span className="layout-athlete-tabs__icon" aria-hidden="true">
                {tab.icon}
              </span>
              <span className="layout-athlete-tabs__label-full">{tab.label}</span>
              <span className="layout-athlete-tabs__label-short">{tab.shortLabel ?? tab.label}</span>
              {tab.id === "chat" && hasUnreadChat ? (
                <span className="layout-athlete-tabs__dot" aria-label="Непрочитанные" />
              ) : null}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );
}
