/*
 * Contexto de sesion (SPEC-008, RF-13/RF-14).
 * Estado: `checking | anonymous | authenticated`. Al arrancar, si hay token se
 * valida con `GET /auth/sesion` (401 -> limpia y anonimo). Un evento de sesion
 * vencida (emitido por el cliente ante un 401) devuelve el estado a anonimo sin
 * perder la vista montada: el overlay de login aparece encima.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import {
  SESSION_EXPIRED_EVENT,
  clearToken,
  getToken,
  login as loginRequest,
  logout as logoutRequest,
  session as fetchSession,
  setToken,
} from "../api";
import type { Role } from "../api";

export interface AuthUser {
  usuario: string;
  nombre: string;
  roles: Role[];
}

export type AuthStatus = "checking" | "anonymous" | "authenticated";

export interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  login: (usuario: string, contrasena: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: Role) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }
  return context;
}

function toUser(profile: {
  usuario: string;
  nombre: string;
  roles: Role[];
}): AuthUser {
  return { usuario: profile.usuario, nombre: profile.nombre, roles: profile.roles };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>(() =>
    getToken() === null ? "anonymous" : "checking",
  );
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    if (getToken() === null) {
      setStatus("anonymous");
      setUser(null);
      return;
    }
    let cancelled = false;
    fetchSession()
      .then((profile) => {
        if (cancelled) {
          return;
        }
        setUser(toUser(profile));
        setStatus("authenticated");
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        clearToken();
        setUser(null);
        setStatus("anonymous");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const handleExpired = () => {
      clearToken();
      setUser(null);
      setStatus("anonymous");
    };
    window.addEventListener(SESSION_EXPIRED_EVENT, handleExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, handleExpired);
  }, []);

  const login = useCallback(async (usuario: string, contrasena: string) => {
    const result = await loginRequest(usuario, contrasena);
    setToken(result.token);
    try {
      const profile = await fetchSession();
      setUser(toUser(profile));
      setStatus("authenticated");
    } catch (error) {
      clearToken();
      setUser(null);
      setStatus("anonymous");
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } catch {
      // Aunque falle la auditoria del backend, se limpia la sesion local.
    } finally {
      clearToken();
      setUser(null);
      setStatus("anonymous");
    }
  }, []);

  const hasRole = useCallback(
    (role: Role) => user !== null && user.roles.includes(role),
    [user],
  );

  const value = useMemo(
    () => ({ status, user, login, logout, hasRole }),
    [status, user, login, logout, hasRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
