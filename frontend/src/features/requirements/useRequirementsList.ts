import { useCallback, useEffect, useState } from "react";

import { listRequirements } from "../../api";
import type { RequirementPage, RequirementStatus } from "../../api";

const DEFAULT_SIZE = 10;

export interface RequirementsListResult {
  data: RequirementPage | null;
  loading: boolean;
  error: Error | null;
  page: number;
  size: number;
  totalPages: number;
  estado: RequirementStatus | "";
  folioInput: string;
  folioError: string | null;
  setEstado: (estado: RequirementStatus | "") => void;
  setFolioInput: (value: string) => void;
  applyFolioFilter: () => void;
  goToPage: (page: number) => void;
  reload: () => void;
}

function parseFolio(value: string): number | null {
  return /^\d+$/.test(value) && Number(value) >= 1 ? Number(value) : null;
}

export function useRequirementsList(): RequirementsListResult {
  const [data, setData] = useState<RequirementPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [page, setPage] = useState(1);
  const [estado, setEstadoState] = useState<RequirementStatus | "">("");
  const [folioInput, setFolioInput] = useState("");
  const [folio, setFolio] = useState<number | undefined>(undefined);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listRequirements({ estado, folio, page, size: DEFAULT_SIZE })
      .then((result) => {
        if (!cancelled) {
          setData(result);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error("Error al listar"));
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
  }, [estado, folio, page, reloadToken]);

  const folioError =
    folioInput !== "" && parseFolio(folioInput) === null
      ? "Ingrese un folio numerico valido."
      : null;

  const setEstado = useCallback((next: RequirementStatus | "") => {
    setEstadoState(next);
    setPage(1);
  }, []);

  const applyFolioFilter = useCallback(() => {
    const parsed = folioInput === "" ? undefined : parseFolio(folioInput) ?? undefined;
    setFolio(parsed);
    setPage(1);
  }, [folioInput]);

  const goToPage = useCallback((next: number) => {
    setPage(next < 1 ? 1 : next);
  }, []);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  const totalPages =
    data !== null ? Math.max(1, Math.ceil(data.total / data.size)) : 1;

  return {
    data,
    loading,
    error,
    page,
    size: DEFAULT_SIZE,
    totalPages,
    estado,
    folioInput,
    folioError,
    setEstado,
    setFolioInput,
    applyFolioFilter,
    goToPage,
    reload,
  };
}
