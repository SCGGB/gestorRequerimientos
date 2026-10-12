import { useEffect, useState } from "react";

export interface VersionResponse {
  version: string;
}

export interface HealthResponse {
  status: string;
  database: string;
}

export interface SystemStatus {
  version: string | null;
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
}

export function useSystemStatus(): SystemStatus {
  const [version, setVersion] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load(): Promise<void> {
      setLoading(true);
      setError(null);
      try {
        const [versionResponse, healthResponse] = await Promise.all([
          fetch("/version"),
          fetch("/health"),
        ]);
        if (!versionResponse.ok || !healthResponse.ok) {
          throw new Error("El backend respondio un estado inesperado");
        }
        const [versionData, healthData] = (await Promise.all([
          versionResponse.json(),
          healthResponse.json(),
        ])) as [VersionResponse, HealthResponse];
        if (cancelled) {
          return;
        }
        setVersion(versionData.version);
        setHealth(healthData);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Error al consultar el backend",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { version, health, loading, error };
}