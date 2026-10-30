import { jsonBody, req } from "@/shared/api/client";
import { Rol } from "@/features/auth/api";

export interface Member {
  id: string;
  email: string;
  nombre: string;
  rol: Rol;
  activo: boolean;
  debe_cambiar_password: boolean;
  created_at: string;
}

export const orgApi = {
  list: () => req<Member[]>("/org/members"),
  create: (body: { email: string; nombre: string; rol: Rol }) =>
    req<{ member: Member; password_temporal: string }>("/org/members", { method: "POST", ...jsonBody(body) }),
  update: (id: string, body: { rol?: Rol; activo?: boolean }) =>
    req<Member>(`/org/members/${id}`, { method: "PATCH", ...jsonBody(body) }),
};
