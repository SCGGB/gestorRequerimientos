import { useCallback, useEffect, useState } from "react";

import { downloadDocument, generateDocuments, listDocuments } from "../api";
import type { GeneratedDocument } from "../api";

export interface RequirementDocumentsResult {
  data: GeneratedDocument[];
  loading: boolean;
  error: Error | null;
  generate: () => Promise<GeneratedDocument[] | null>;
  download: (documentId: number) => Promise<void>;
  reload: () => void;
}

function toError(error: unknown, fallback: string): Error {
  return error instanceof Error ? error : new Error(fallback);
}

function triggerDownload(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function useRequirementDocuments(
  requirementId: number | null,
): RequirementDocumentsResult {
  const [data, setData] = useState<GeneratedDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (requirementId === null) {
      setData([]);
      setError(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listDocuments(requirementId, controller.signal)
      .then((documents) => {
        if (!controller.signal.aborted) {
          setData(documents);
        }
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            toError(err, "No fue posible cargar los documentos generados."),
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
  }, [requirementId, reloadToken]);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  const generate = useCallback(async (): Promise<GeneratedDocument[] | null> => {
    if (requirementId === null) {
      return null;
    }
    setLoading(true);
    setError(null);
    try {
      const documents = await generateDocuments(requirementId);
      setReloadToken((token) => token + 1);
      return documents;
    } catch (err: unknown) {
      setError(toError(err, "No fue posible generar los documentos."));
      return null;
    } finally {
      setLoading(false);
    }
  }, [requirementId]);

  const download = useCallback(
    async (documentId: number): Promise<void> => {
      if (requirementId === null) {
        return;
      }
      setError(null);
      try {
        const { blob, fileName } = await downloadDocument(
          requirementId,
          documentId,
        );
        triggerDownload(blob, fileName);
      } catch (err: unknown) {
        setError(toError(err, "No fue posible descargar el documento."));
      }
    },
    [requirementId],
  );

  return { data, loading, error, generate, download, reload };
}
