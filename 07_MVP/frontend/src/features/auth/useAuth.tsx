import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { getToken, setToken, setUnauthorizedHandler } from "@/shared/api/client";
import { authApi, User } from "./api";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, nombre: string, empresa: string) => Promise<void>;
  logout: () => void;
  changePassword: (actual: string, nueva: string) => Promise<void>;
  /** Mensaje del 401 que cerró la sesión (p. ej. cuenta desactivada); LoginPage lo muestra una vez. */
  sessionNotice: string;
  clearSessionNotice: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionNotice, setSessionNotice] = useState("");

  useEffect(() => {
    setUnauthorizedHandler((detail) => {
      setSessionNotice(detail);
      setToken(null);
      setUser(null);
    });
    if (!getToken()) {
      setLoading(false);
      return;
    }
    authApi.me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const { token, user } = await authApi.login({ email, password });
    setToken(token);
    setUser(user);
  }

  async function signup(email: string, password: string, nombre: string, empresa: string) {
    const { token, user } = await authApi.signup({ email, password, nombre, empresa });
    setToken(token);
    setUser(user);
  }

  async function changePassword(password_actual: string, password_nueva: string) {
    const { user } = await authApi.changePassword({ password_actual, password_nueva });
    setUser(user);
  }

  function logout() {
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{
      user, loading, isAuthenticated: !!user, login, signup, logout, changePassword,
      sessionNotice, clearSessionNotice: () => setSessionNotice(""),
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
