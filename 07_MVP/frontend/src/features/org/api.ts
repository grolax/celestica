import { jsonBody, req } from "@/shared/api/client";
import { Organizacion, Rol } from "@/features/auth/api";

export interface Member {
  id: string;
  email: string;
  nombre: string;
  rol: Rol;
  activo: boolean;
  debe_cambiar_password: boolean;
  created_at: string;
}

/** Lista cerrada del contrato RF-10 (texto exacto). */
export const RUBROS = [
  "Educación Superior",
  "Estudios de Mercado",
  "Organizaciones y B2B",
  "Sector Público",
  "Salud",
  "Retail",
  "Municipal",
  "Otro",
];

export const orgApi = {
  list: () => req<Member[]>("/org/members"),
  create: (body: { email: string; nombre: string; rol: Rol }) =>
    req<{ member: Member; password_temporal: string }>("/org/members", { method: "POST", ...jsonBody(body) }),
  update: (id: string, body: { rol?: Rol; activo?: boolean }) =>
    req<Member>(`/org/members/${id}`, { method: "PATCH", ...jsonBody(body) }),
  updateProfile: (body: { nombre: string; rubro: string | null; color: string | null }) =>
    req<Organizacion>("/org/profile", { method: "PUT", ...jsonBody(body) }),
  uploadLogo: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return req<Organizacion>("/org/logo", { method: "PUT", body: form });
  },
  getLogo: () => req<{ logo: string }>("/org/logo"),
  deleteLogo: () => req<Organizacion>("/org/logo", { method: "DELETE" }),
};
