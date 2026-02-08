import React, { createContext, useContext, useCallback } from "react";
import { User } from "../types";
import { authAPI, setCurrentAccessToken } from "../api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (identifier: string, password: string) => Promise<void>;
  register: (
    email: string,
    username: string,
    password: string,
  ) => Promise<void>;
  tryItNow: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = React.useState<User | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const initAuth = async () => {
      try {
        setLoading(true);
        const tokens = await authAPI.refresh();
        setCurrentAccessToken(tokens.access_token);
        const userData = await authAPI.me(tokens.access_token);
        setUser(userData);
        setError(null);
      } catch (err) {
        // Not logged in, that's fine
        setUser(null);
        setCurrentAccessToken(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (identifier: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const tokens = await authAPI.login(identifier, password);
      setCurrentAccessToken(tokens.access_token);

      const userData = await authAPI.me(tokens.access_token);
      setUser(userData);
      setError(null);
    } catch (err: any) {
      const message =
        err?.response?.data?.detail || err?.message || "Login failed";
      setError(message);
      setUser(null);
      setCurrentAccessToken(null);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(
    async (email: string, username: string, password: string) => {
      setLoading(true);
      setError(null);
      try {
        const tokens = await authAPI.register(email, username, password);
        setCurrentAccessToken(tokens.access_token);

        const userData = await authAPI.me(tokens.access_token);
        setUser(userData);
        setError(null);
      } catch (err: any) {
        const message =
          err?.response?.data?.detail || err?.message || "Registration failed";
        setError(message);
        setUser(null);
        setCurrentAccessToken(null);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const tryItNow = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const tokens = await authAPI.tryItNow();
      setCurrentAccessToken(tokens.access_token);

      const userData = await authAPI.me(tokens.access_token);
      setUser(userData);
      setError(null);
    } catch (err: any) {
      const message =
        err?.response?.data?.detail || err?.message || "Try it now failed";
      setError(message);
      setUser(null);
      setCurrentAccessToken(null);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authAPI.logout();
    } catch (err) {
      console.error("Logout failed:", err);
    }
    setUser(null);
    setCurrentAccessToken(null);
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        login,
        register,
        tryItNow,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
