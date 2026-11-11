import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { getToken, setToken, setUnauthorizedHandler } from "@/shared/api/client";
import { authApi, Organizacion, User } from "./api";
import { orgApi } from "@/features/org/api";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, nombre: string, empresa: string) => Promise<void>;
  logout: () => void;
  changePassword: (actual: string, nueva: string) => Promise<void>;
  /** Data URL del logo de la organización (se pide una vez por sesión), o null si no tiene. */
  logo: string | null;
  /** Reemplaza `user.organizacion` con lo que devolvió el servidor; `logoCambio` vuelve a pedir el logo. */
  setOrganizacion: (org: Organizacion, logoCambio?: boolean) => void;
  /** Mensaje del 401 que cerró la sesión (p. ej. cuenta desactivada); LoginPage lo muestra una vez. */
  sessionNotice: string;
  clearSessionNotice: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionNotice, setSessionNotice] = useState("");
  const [logo, setLogo] = useState<string | null>(null);
  const [logoVersion, setLogoVersion] = useState(0);

  const orgId = user?.organizacion?.id;
  const tieneLogo = user?.organizacion?.tiene_logo ?? false;
  useEffect(() => {
    if (!tieneLogo) { setLogo(null); return; }
    orgApi.getLogo().then((r) => setLogo(r.logo)).catch(() => setLogo(null));
  }, [orgId, tieneLogo, logoVersion]);

  function setOrganizacion(org: Organizacion, logoCambio = false) {
    setUser((u) => u && { ...u, organizacion: org });
    if (logoCambio) setLogoVersion((v) => v + 1);
  }

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
      logo, setOrganizacion, sessionNotice, clearSessionNotice: () => setSessionNotice(""),
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
