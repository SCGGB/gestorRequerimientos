/*
 * Gestion de usuarios (SPEC-008, RF-08/RF-09, CA-08/CA-09). Solo visible para
 * ADMIN; el backend enforce igual con 403. Alta, edicion de roles/credenciales y
 * baja logica (activo=false). La edicion siempre reinicia los intentos fallidos.
 */

import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError, ROLE_LABELS, createUser, updateUser } from "../../api";
import type { Role, Usuario } from "../../api";
import { useAuth } from "../../auth/AuthContext";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { useUsers } from "./useUsers";

const ROLES: Role[] = ["ELABORO", "REVISO", "AUTORIZO", "ADMIN"];
const MAX_FAILED_ATTEMPTS = 5;

interface FormState {
  usuario: string;
  nombre: string;
  contrasena: string;
  roles: Role[];
  activo: boolean;
}

const EMPTY_FORM: FormState = {
  usuario: "",
  nombre: "",
  contrasena: "",
  roles: [],
  activo: true,
};

function messageFor(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case "username_taken":
        return "El usuario ya existe.";
      case "self_deactivation_not_allowed":
        return "No puede desactivar su propio usuario.";
      case "user_not_found":
        return "El usuario ya no existe.";
      default:
        return error.message;
    }
  }
  return "No fue posible completar la operacion.";
}

function toggleRole(roles: Role[], role: Role): Role[] {
  return roles.includes(role)
    ? roles.filter((item) => item !== role)
    : [...roles, role];
}

export function UsersPage() {
  const { user } = useAuth();
  const { data, loading, error, reload } = useUsers();
  const [mode, setMode] = useState<"closed" | "create" | "edit">("closed");
  const [editing, setEditing] = useState<Usuario | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const isSelf = editing !== null && editing.usuario === user?.usuario;

  function openCreate() {
    setMode("create");
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
  }

  function openEdit(target: Usuario) {
    setMode("edit");
    setEditing(target);
    setForm({
      usuario: target.usuario,
      nombre: target.nombre,
      contrasena: "",
      roles: [...target.roles],
      activo: target.activo,
    });
    setFormError(null);
  }

  function closeForm() {
    setMode("closed");
    setEditing(null);
    setFormError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      if (mode === "create") {
        await createUser({
          usuario: form.usuario,
          nombre: form.nombre,
          contrasena: form.contrasena,
          roles: form.roles,
          activo: form.activo,
        });
      } else if (editing !== null) {
        await updateUser(editing.id, {
          nombre: form.nombre,
          roles: form.roles,
          activo: form.activo,
          ...(form.contrasena === "" ? {} : { contrasena: form.contrasena }),
        });
      }
      closeForm();
      reload();
    } catch (err) {
      setFormError(messageFor(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="mx-auto flex w-full max-w-4xl flex-col gap-6">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-secondary">
            Gestion de usuarios
          </h1>
          <p className="text-sm text-neutral-dark">
            Alta, edicion de roles y bloqueo de acceso.
          </p>
        </div>
        <Button onClick={openCreate}>Nuevo usuario</Button>
      </header>

      {error !== null && (
        <p role="alert" className="text-sm text-danger">
          {error.message}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-neutral-dark">Cargando usuarios...</p>
      ) : (
        <div className="overflow-x-auto rounded border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted text-xs uppercase tracking-wide text-neutral-dark">
              <tr>
                <th className="px-3 py-2">Usuario</th>
                <th className="px-3 py-2">Nombre</th>
                <th className="px-3 py-2">Roles</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2">Intentos</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.id} className="border-t border-border">
                  <td className="px-3 py-2 font-medium text-secondary">
                    {item.usuario}
                  </td>
                  <td className="px-3 py-2">{item.nombre}</td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {item.roles.map((role) => (
                        <Badge key={role} label={ROLE_LABELS[role]} />
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <Badge
                      label={item.activo ? "Activo" : "Inactivo"}
                      tone={item.activo ? "success" : "danger"}
                    />
                  </td>
                  <td className="px-3 py-2">
                    {item.intentos_fallidos >= MAX_FAILED_ATTEMPTS ? (
                      <Badge label="Bloqueado" tone="warning" />
                    ) : (
                      item.intentos_fallidos
                    )}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openEdit(item)}
                    >
                      Editar
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {mode !== "closed" && (
        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-4 rounded border border-border bg-surface p-4"
        >
          <h2 className="text-base font-semibold text-secondary">
            {mode === "create" ? "Nuevo usuario" : `Editar ${form.usuario}`}
          </h2>

          {mode === "create" && (
            <Input
              label="Usuario"
              value={form.usuario}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, usuario: event.target.value }))
              }
              required
            />
          )}

          <Input
            label="Nombre"
            value={form.nombre}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, nombre: event.target.value }))
            }
            required
          />

          <Input
            label={
              mode === "create" ? "Contrasena" : "Contrasena (dejar vacio para conservar)"
            }
            type="password"
            minLength={8}
            value={form.contrasena}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, contrasena: event.target.value }))
            }
            required={mode === "create"}
            hint="Minimo 8 caracteres."
          />

          <fieldset className="flex flex-col gap-2">
            <legend className="text-sm font-semibold text-neutral-dark">
              Roles
            </legend>
            <div className="flex flex-wrap gap-4">
              {ROLES.map((role) => (
                <label key={role} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.roles.includes(role)}
                    onChange={() =>
                      setForm((prev) => ({
                        ...prev,
                        roles: toggleRole(prev.roles, role),
                      }))
                    }
                  />
                  {ROLE_LABELS[role]}
                </label>
              ))}
            </div>
          </fieldset>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.activo}
              disabled={isSelf}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, activo: event.target.checked }))
              }
            />
            Activo
            {isSelf && (
              <span className="text-xs text-neutral-dark">
                (no puede desactivar su propio usuario)
              </span>
            )}
          </label>

          {mode === "edit" && (
            <p className="text-xs text-neutral-dark">
              Al guardar se reinician los intentos de acceso del usuario.
            </p>
          )}

          {formError !== null && (
            <p role="alert" className="text-sm text-danger">
              {formError}
            </p>
          )}

          <div className="flex gap-2">
            <Button type="submit" disabled={submitting}>
              {submitting ? "Guardando..." : "Guardar"}
            </Button>
            <Button variant="secondary" onClick={closeForm}>
              Cancelar
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}
