import { request } from "./client";
import type { LoginResponse, SesionResponse } from "./types";

export function login(
  usuario: string,
  contrasena: string,
): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: { usuario, contrasena },
  });
}

export function logout(): Promise<void> {
  return request<void>("/auth/logout", { method: "POST" });
}

export function session(signal?: AbortSignal): Promise<SesionResponse> {
  return request<SesionResponse>("/auth/sesion", { signal });
}
