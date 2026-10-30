import { jsonBody, req } from "@/shared/api/client";

export type Rol = "admin" | "analista" | "lector";

export const ROL_LABEL: Record<Rol, string> = {
  admin: "Administrador",
  analista: "Analista",
  lector: "Lector",
};

export interface User {
  id: string;
  email: string;
  nombre: string;
  empresa: string;
  rol: Rol;
  organizacion: { id: string; nombre: string };
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
};
