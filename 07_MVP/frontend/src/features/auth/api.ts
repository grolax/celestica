import { jsonBody, req } from "@/shared/api/client";

export type Rol = "admin" | "analista" | "lector";

export const ROL_LABEL: Record<Rol, string> = {
  admin: "Administrador",
  analista: "Analista",
  lector: "Lector",
};

const ORDEN: Record<Rol, number> = { lector: 0, analista: 1, admin: 2 };

/** Solo refleja permisos en la UI (el backend valida). Un rol desconocido cuenta como lector. */
export function puede(user: User | null | undefined, minimo: Rol): boolean {
  return (ORDEN[user?.rol as Rol] ?? 0) >= ORDEN[minimo];
}

export interface User {
  id: string;
  email: string;
  nombre: string;
  empresa: string;
  rol: Rol;
  organizacion: { id: string; nombre: string };
  debe_cambiar_password: boolean;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export const authApi = {
  signup: (body: { email: string; password: string; nombre: string; empresa: string }) =>
    req<AuthResponse>("/signup", { method: "POST", ...jsonBody(body) }, "/auth"),
  login: (body: { email: string; password: string }) =>
    req<AuthResponse>("/login", { method: "POST", ...jsonBody(body) }, "/auth"),
  me: () => req<User>("/me", {}, "/auth"),
  changePassword: (body: { password_actual: string; password_nueva: string }) =>
    req<{ user: User }>("/change-password", { method: "POST", ...jsonBody(body) }, "/auth"),
};
