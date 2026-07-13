import { jsonBody, req } from "@/shared/api/client";

export interface User {
  id: string;
  email: string;
  nombre: string;
  empresa: string;
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
