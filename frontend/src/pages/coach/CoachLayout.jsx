import { useCallback, useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../auth/AuthContext.jsx";
import { CoachShell } from "../../components/layout/CoachShell.jsx";
import { Avatar } from "../../components/ui/Avatar.jsx";
import {
  COACH_NAV_ITEMS,
  isCoachCustomHeaderRoute,
  resolveCoachNavId,
  resolveCoachNavPath,
  resolveCoachPageTitle,
} from "../../components/coach/coachTabs.js";
import { fetchCoachConversations } from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";

function buildCoachDisplayName(user) {
  if (!user?.email) {
    return "Тренер";
  }
  const localPart = user.email.split("@")[0] ?? "Тренер";
  const normalized = localPart.replace(/[._]/g, " ");
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

export function CoachLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  const activeNav = resolveCoachNavId(location.pathname);
  const hideHeader = isCoachCustomHeaderRoute(location.pathname);
  const displayName = buildCoachDisplayName(user);

  const loadUnreadCount = useCallback(async () => {
    try {
      const token = getToken();
      const result = await fetchCoachConversations(token);
      const total = result.items.reduce((sum, item) => sum + (item.unread_count ?? 0), 0);
      setUnreadCount(total);
    } catch {
      setUnreadCount(0);
    }
  }, []);

  useEffect(() => {
    loadUnreadCount();
  }, [loadUnreadCount, location.pathname]);

  function handleNavChange(navId) {
    navigate(resolveCoachNavPath(navId));
  }

  return (
    <CoachShell
      title={hideHeader ? null : resolveCoachPageTitle(location.pathname)}
      hideHeader={hideHeader}
      activeNav={activeNav}
      onNavChange={handleNavChange}
      unreadCount={unreadCount}
      userName={displayName}
      onLogout={logout}
      footer={
        <div className="layout-coach-sidebar__user">
          <Avatar initials={displayName.slice(0, 2).toUpperCase()} size="md" />
          <div>
            <p className="layout-coach-sidebar__user-name">{displayName}</p>
            <p className="layout-coach-sidebar__user-role">Тренер</p>
          </div>
        </div>
      }
    >
      <Outlet />
    </CoachShell>
  );
}

export { COACH_NAV_ITEMS };
