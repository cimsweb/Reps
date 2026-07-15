import { useCallback, useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { fetchAthleteConversations } from "../../api/client.js";
import { useAuth } from "../../auth/AuthContext.jsx";
import { getToken } from "../../auth/tokenStorage.js";
import { AthleteShell } from "../../components/layout/AthleteShell.jsx";
import {
  resolveAthleteTabId,
  resolveAthleteTabPath,
} from "../../components/athlete/athleteTabs.js";
import { buildAthleteDisplayName } from "../../utils/athleteDisplayName.js";
import { AthleteDayProvider } from "./AthleteDayContext.jsx";

export function AthleteLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [hasUnreadChat, setHasUnreadChat] = useState(false);

  const activeTab = resolveAthleteTabId(location.pathname);
  const displayName = buildAthleteDisplayName(user);

  const loadUnreadChat = useCallback(async () => {
    try {
      const token = getToken();
      const result = await fetchAthleteConversations(token);
      const total = result.items.reduce((sum, item) => sum + (item.unread_count ?? 0), 0);
      setHasUnreadChat(total > 0);
    } catch {
      setHasUnreadChat(false);
    }
  }, []);

  useEffect(() => {
    loadUnreadChat();
  }, [loadUnreadChat, location.pathname]);

  function handleTabChange(tabId) {
    navigate(resolveAthleteTabPath(tabId));
  }

  return (
    <AthleteDayProvider>
      <AthleteShell
        userName={displayName}
        activeTab={activeTab}
        onTabChange={handleTabChange}
        hasUnreadChat={hasUnreadChat}
        onLogout={logout}
      >
        <Outlet />
      </AthleteShell>
    </AthleteDayProvider>
  );
}
