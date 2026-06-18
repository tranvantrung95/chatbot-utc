"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { UserRole } from "@/lib/types";
import { apiChangePassword, apiLogin, apiLogout, apiMe, type ApiUser } from "@/lib/api-client";

const TOKEN_KEY = "utc-token";

type AuthContextType = {
  user: ApiUser | null;
  role: UserRole | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (identifier: string, password: string) => Promise<ApiUser>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<string>;
};

const AuthContext = createContext<AuthContextType | null>(null);

function roleLabel(role: UserRole | null) {
  if (role === "admin") return "Quản trị viên";
  if (role === "student") return "Sinh viên";
  return "Chưa xác định";
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<ApiUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearAuth = useCallback(() => {
    setUser(null);
    setToken(null);
    window.localStorage.removeItem(TOKEN_KEY);
  }, []);

  const refreshProfile = useCallback(async () => {
    const savedToken = token || window.localStorage.getItem(TOKEN_KEY);
    if (!savedToken) {
      clearAuth();
      return;
    }
    try {
      const response = await apiMe(savedToken);
      setToken(savedToken);
      setUser(response.user);
      window.localStorage.setItem(TOKEN_KEY, savedToken);
    } catch {
      clearAuth();
      throw new Error("Phiên đăng nhập đã hết hạn.");
    }
  }, [clearAuth, token]);

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const savedToken = window.localStorage.getItem(TOKEN_KEY);
        if (!savedToken) {
          clearAuth();
          return;
        }
        const response = await apiMe(savedToken);
        setToken(savedToken);
        setUser(response.user);
      } catch {
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    };
    void bootstrap();
  }, [clearAuth]);

  const login = useCallback(async (identifier: string, password: string) => {
    const response = await apiLogin(identifier, password);
    setToken(response.token);
    setUser(response.user);
    window.localStorage.setItem(TOKEN_KEY, response.token);
    return response.user;
  }, []);

  const logout = useCallback(async () => {
    const currentToken = token || window.localStorage.getItem(TOKEN_KEY);
    try {
      if (currentToken) await apiLogout(currentToken);
    } catch {
      // Cleanup local session even if backend is unavailable.
    } finally {
      clearAuth();
    }
  }, [clearAuth, token]);

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      const activeToken = token || window.localStorage.getItem(TOKEN_KEY);
      if (!activeToken) throw new Error("Bạn chưa đăng nhập.");
      const response = await apiChangePassword(activeToken, currentPassword, newPassword);
      return response.message;
    },
    [token],
  );

  const value = useMemo(
    () => ({
      user,
      role: user?.role || null,
      token,
      isAuthenticated: Boolean(user && token),
      isLoading,
      login,
      logout,
      refreshProfile,
      changePassword,
    }),
    [changePassword, isLoading, login, logout, refreshProfile, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth phải được dùng trong AuthProvider.");
  return context;
}

export { roleLabel };
