import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { tokenStorage } from "../lib/tokenStorage";
import { fetchCurrentUser, login as loginRequest, logout as logoutRequest, register as registerRequest } from "../lib/authApi";
import type { AuthUser, LoginCredentials, RegisterPayload, RegisterResponse } from "../types";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<RegisterResponse>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!tokenStorage.getAccess()) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const me = await fetchCurrentUser();
      setUser(me);
    } catch {
      tokenStorage.clear();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadUser();
  }, [loadUser]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const tokens = await loginRequest(credentials);
    tokenStorage.set(tokens);
    const me = await fetchCurrentUser();
    setUser(me);
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    const response = await registerRequest(payload);
    if (response.access && response.refresh) {
      tokenStorage.set({ access: response.access, refresh: response.refresh });
      const me = await fetchCurrentUser();
      setUser(me);
    }
    return response;
  }, []);

  const logout = useCallback(async () => {
    const refresh = tokenStorage.getRefresh();
    try {
      if (refresh) {
        await logoutRequest(refresh);
      }
    } catch {
      // ignore — token may already be invalid/expired
    } finally {
      tokenStorage.clear();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: user !== null, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
