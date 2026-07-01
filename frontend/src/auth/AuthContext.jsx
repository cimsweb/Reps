import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { fetchCurrentUser, loginUser, logoutUser, registerUser } from "../api/client.js";
import { clearToken, getToken, setToken } from "./tokenStorage.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const currentUser = await fetchCurrentUser(token);
      setUser(currentUser);
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(async (email, password) => {
    const result = await loginUser({ email, password });
    setToken(result.token);
    setUser(result.user);
    return result.user;
  }, []);

  const register = useCallback(async (email, password, role) => {
    await registerUser({ email, password, role });
  }, []);

  const logout = useCallback(async () => {
    const token = getToken();
    if (token) {
      try {
        await logoutUser(token);
      } catch {
        // Session may already be invalid; clear local state anyway.
      }
    }
    clearToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      reloadUser: loadUser,
    }),
    [user, loading, login, register, logout, loadUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
