/*
 * Autosave con debounce para cabecera/narrativa de la version (SPEC-004, RF-12).
 * Las escrituras se serializan por requerimiento+version: una cola simple evita
 * PATCH concurrentes sobre la misma version. Tras cada guardado se notifica el
 * `VersionResponse` devuelto para refrescar el estado del wizard.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { updateVersion } from "../api";
import type { VersionResponse, VersionUpdatePayload } from "../api";

const DEFAULT_DELAY = 800;

const writeQueues = new Map<string, Promise<void>>();

function enqueueWrite(key: string, task: () => Promise<void>): Promise<void> {
  const previous = writeQueues.get(key) ?? Promise.resolve();
  const next = previous.then(task, task).catch(() => undefined);
  writeQueues.set(key, next);
  void next.finally(() => {
    if (writeQueues.get(key) === next) {
      writeQueues.delete(key);
    }
  });
  return next;
}

export interface AutosaveOptions {
  requirementId: number | null;
  versionId: number | null;
  delay?: number;
  enabled?: boolean;
  onSaved?: (version: VersionResponse) => void;
  onError?: (error: Error) => void;
}

export interface AutosaveController {
  schedule: (payload: VersionUpdatePayload) => void;
  saveNow: (payload: VersionUpdatePayload) => Promise<VersionResponse | null>;
  flush: () => Promise<VersionResponse | null>;
  dirty: boolean;
  saving: boolean;
  error: Error | null;
}

export function useAutosave(options: AutosaveOptions): AutosaveController {
  const { requirementId, versionId } = options;

  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const payloadRef = useRef<VersionUpdatePayload | null>(null);
  const lastSavedRef = useRef<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const optionsRef = useRef(options);
  const mountedRef = useRef(true);

  useEffect(() => {
    optionsRef.current = options;
  });

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    payloadRef.current = null;
    lastSavedRef.current = null;
    setDirty(false);
  }, [requirementId, versionId]);

  const run = useCallback(async (): Promise<VersionResponse | null> => {
    const payload = payloadRef.current;
    const { requirementId: reqId, versionId: verId } = optionsRef.current;
    if (payload === null || reqId === null || verId === null) {
      return null;
    }
    const serialized = JSON.stringify(payload);
    if (serialized === lastSavedRef.current) {
      return null;
    }
    const key = `${reqId}:${verId}`;
    setSaving(true);
    let saved: VersionResponse | null = null;
    await enqueueWrite(key, async () => {
      try {
        const version = await updateVersion(reqId, verId, payload);
        saved = version;
        lastSavedRef.current = serialized;
        if (mountedRef.current) {
          setError(null);
          setDirty(
            payloadRef.current !== null && JSON.stringify(payloadRef.current) !== serialized,
          );
        }
        optionsRef.current.onSaved?.(version);
      } catch (err) {
        const normalized =
          err instanceof Error ? err : new Error("Error al guardar el borrador");
        if (mountedRef.current) {
          setError(normalized);
        }
        optionsRef.current.onError?.(normalized);
      } finally {
        if (mountedRef.current) {
          setSaving(false);
        }
      }
    });
    return saved;
  }, []);

  const schedule = useCallback(
    (payload: VersionUpdatePayload) => {
      if (optionsRef.current.enabled === false) {
        return;
      }
      const { requirementId: reqId, versionId: verId } = optionsRef.current;
      payloadRef.current = { ...(payloadRef.current ?? {}), ...payload };
      if (reqId === null || verId === null) {
        return;
      }
      setDirty(JSON.stringify(payloadRef.current) !== lastSavedRef.current);
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
      }
      timerRef.current = setTimeout(() => {
        timerRef.current = null;
        void run();
      }, optionsRef.current.delay ?? DEFAULT_DELAY);
    },
    [run],
  );

  const saveNow = useCallback(
    async (payload: VersionUpdatePayload): Promise<VersionResponse | null> => {
      payloadRef.current = { ...(payloadRef.current ?? {}), ...payload };
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return run();
    },
    [run],
  );

  const flush = useCallback(async (): Promise<VersionResponse | null> => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    return run();
  }, [run]);

  return useMemo(
    () => ({ schedule, saveNow, flush, dirty, saving, error }),
    [schedule, saveNow, flush, dirty, saving, error],
  );
}
