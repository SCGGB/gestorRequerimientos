/*
 * Overlay de login (SPEC-008, RF-13/RF-14).
 * Se renderiza a pantalla completa **encima** del arbol de la aplicacion, sin
 * desmontarlo: la vista y la navegacion en estado se conservan al expirar la
 * sesion o al entrar sin credenciales.
 */

import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError } from "../api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { useAuth } from "./AuthContext";

function messageFor(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case "invalid_credentials":
        return "Usuario o contrasena incorrectos.";
      case "account_locked":
        return "La cuenta esta bloqueada tras varios intentos fallidos. Contacte al administrador.";
      default:
        return error.message;
    }
  }
  return "No fue posible iniciar sesion. Intente de nuevo.";
}

export function LoginOverlay() {
  const { status, login } = useAuth();
  const [usuario, setUsuario] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(usuario, contrasena);
      setContrasena("");
    } catch (err) {
      setError(messageFor(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      data-testid="login-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Inicio de sesion"
      className="fixed inset-0 z-50 flex items-center justify-center bg-secondary/60 p-4"
    >
      <div className="w-full max-w-sm rounded-lg border border-border bg-surface p-6 shadow-lg">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded bg-primary text-sm font-bold text-on-primary">
            SC
          </div>
          <div className="leading-tight">
            <p className="text-base font-semibold text-secondary">
              Gestor de Requerimientos
            </p>
            <p className="text-xs text-neutral-dark">Inicio de sesion</p>
          </div>
        </div>

        {status === "checking" ? (
          <p className="py-6 text-center text-sm text-neutral-dark">
            Verificando sesion...
          </p>
        ) : (
          <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
            <Input
              label="Usuario"
              name="usuario"
              autoComplete="username"
              value={usuario}
              onChange={(event) => setUsuario(event.target.value)}
              required
            />
            <Input
              label="Contrasena"
              name="contrasena"
              type="password"
              autoComplete="current-password"
              value={contrasena}
              onChange={(event) => setContrasena(event.target.value)}
              required
            />
            {error !== null && (
              <p role="alert" className="text-sm text-danger">
                {error}
              </p>
            )}
            <Button type="submit" disabled={submitting}>
              {submitting ? "Ingresando..." : "Ingresar"}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
