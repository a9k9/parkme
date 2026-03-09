/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
  type ReactElement,
} from "react";
import { Navigate, useLocation } from "react-router-dom";

import { apiAuthTokenCreate } from "@/api/generated/api/api";
import {
  AUTH_LOGIN_EVENT,
  AUTH_LOGOUT_EVENT,
  clearTokens,
  getAccessToken,
  hasTokens,
  setTokens,
} from "@/lib/auth";

type AuthContextValue = {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(
    getAccessToken(),
  );
  const [isLoading, setIsLoading] = useState(false);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await apiAuthTokenCreate({ email, password });
      const tokens = response.data;
      setTokens(tokens);
      setAccessToken(tokens.access);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setAccessToken(null);
  }, []);

  useEffect(() => {
    const syncFromStorage = () => {
      setAccessToken(getAccessToken());
    };

    window.addEventListener(AUTH_LOGIN_EVENT, syncFromStorage);
    window.addEventListener(AUTH_LOGOUT_EVENT, syncFromStorage);

    return () => {
      window.removeEventListener(AUTH_LOGIN_EVENT, syncFromStorage);
      window.removeEventListener(AUTH_LOGOUT_EVENT, syncFromStorage);
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(accessToken) || hasTokens(),
      isLoading,
      login,
      logout,
    }),
    [accessToken, isLoading, login, logout],
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

export function RequireAuth({ children }: { children: ReactElement }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
