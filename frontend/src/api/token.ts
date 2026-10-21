/*
 * Almacenamiento del token de sesion (SPEC-008, RF-13).
 * Sin refresh token: la expiracion la resuelve el backend con 401 y el frontend
 * limpia el token y muestra el overlay de login. `localStorage` sobrevive a
 * recargas de la pestana.
 */

const TOKEN_KEY = "gestor.auth.token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Almacenamiento no disponible: la sesion no persiste entre recargas.
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Sin token que limpiar.
  }
}
