import { useCallback, useEffect, useState } from "react";

import { getPreview } from "../api";
import type { PreviewDocument } from "../api";

export interface PreviewResult {
  data: PreviewDocument | null;
  loading: boolean;
  error: Error | null;
  reload: () => void;
}

export function usePreview(
  requirementId: number | null,
  versionId: number | null,
): PreviewResult {
  const [data, setData] = useState<PreviewDocument | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (requirementId === null || versionId === null) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getPreview(requirementId, versionId, controller.signal)
      .then((document) => {
        if (!controller.signal.aborted) {
          setData(document);
        }
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err
              : new Error("Error al cargar la vista previa"),
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });
    return () => {
      controller.abort();
    };
  }, [requirementId, versionId, reloadToken]);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  return { data, loading, error, reload };
}
