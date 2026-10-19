/*
 * Catalogos de lectura (SPEC-004, RF-13): tipos de cambio y cargos por rol.
 */

import { useEffect, useState } from "react";

import { listChangeTypes, listPositions } from "../api";
import type { ChangeTypeResponse, PositionResponse, SignatureRole } from "../api";

export interface CatalogState<T> {
  data: T[];
  loading: boolean;
  error: string | null;
}

export function useChangeTypes(): CatalogState<ChangeTypeResponse> {
  const [state, setState] = useState<CatalogState<ChangeTypeResponse>>({
    data: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    setState({ data: [], loading: true, error: null });
    listChangeTypes()
      .then((data) => {
        if (!cancelled) {
          setState({ data, loading: false, error: null });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            data: [],
            loading: false,
            error: err instanceof Error ? err.message : "No se pudo cargar el catalogo.",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

export function usePositions(rol?: SignatureRole): CatalogState<PositionResponse> {
  const [state, setState] = useState<CatalogState<PositionResponse>>({
    data: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    setState({ data: [], loading: true, error: null });
    listPositions(rol)
      .then((data) => {
        if (!cancelled) {
          setState({ data, loading: false, error: null });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            data: [],
            loading: false,
            error: err instanceof Error ? err.message : "No se pudo cargar el catalogo.",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [rol]);

  return state;
}
