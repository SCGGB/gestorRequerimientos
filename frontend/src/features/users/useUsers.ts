/*
 * Listado de usuarios para la pantalla ADMIN (SPEC-008, RF-08).
 * Patron `{ data, loading, error, reload }` de `useRequirementsList`.
 */

import { useCallback, useEffect, useState } from "react";

import { listUsers } from "../../api";
import type { Usuario } from "../../api";

export interface UsersResult {
  data: Usuario[];
  loading: boolean;
  error: Error | null;
  reload: () => void;
}

export function useUsers(): UsersResult {
  const [data, setData] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listUsers()
      .then((users) => {
        if (!cancelled) {
          setData(users);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err : new Error("Error al listar usuarios"),
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  return { data, loading, error, reload };
}
