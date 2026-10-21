import { request } from "./client";
import type {
  Usuario,
  UsuarioCreatePayload,
  UsuarioUpdatePayload,
} from "./types";

export function listUsers(signal?: AbortSignal): Promise<Usuario[]> {
  return request<Usuario[]>("/usuarios", { signal });
}

export function getUser(id: number, signal?: AbortSignal): Promise<Usuario> {
  return request<Usuario>(`/usuarios/${id}`, { signal });
}

export function createUser(payload: UsuarioCreatePayload): Promise<Usuario> {
  return request<Usuario>("/usuarios", { method: "POST", body: payload });
}

export function updateUser(
  id: number,
  payload: UsuarioUpdatePayload,
): Promise<Usuario> {
  return request<Usuario>(`/usuarios/${id}`, { method: "PATCH", body: payload });
}
