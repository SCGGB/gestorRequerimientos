import { StatusBadge } from "../components/ui/StatusBadge";
import { useSystemStatus } from "../hooks/useSystemStatus";

export function OverviewPage() {
  const { version, health, loading, error } = useSystemStatus();

  const appKey = error
    ? ("danger" as const)
    : loading
      ? ("neutral" as const)
      : health?.status === "ok"
        ? ("success" as const)
        : ("danger" as const);

  const databaseKey = error
    ? ("danger" as const)
    : loading
      ? ("neutral" as const)
      : health?.database === "ok"
        ? ("success" as const)
        : health?.database === "down"
          ? ("danger" as const)
          : ("warning" as const);

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-border bg-surface p-6">
        <h1 className="text-2xl font-semibold text-secondary">
          Estado del sistema
        </h1>
        <p className="mt-2 text-sm text-neutral-dark">
          Version de la aplicacion y salud del backend.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-surface p-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-neutral-dark">
            Version
          </p>
          <p className="mt-3 font-mono text-lg text-secondary">
            {loading ? "..." : version ?? "desconocida"}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-surface p-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-neutral-dark">
            Estado
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <StatusBadge
              label={
                error
                  ? "sin conexion"
                  : loading
                    ? "cargando"
                    : "aplicacion ok"
              }
              tone={appKey}
            />
            <StatusBadge
              label={
                error
                  ? "backend no disponible"
                  : loading
                    ? "cargando"
                    : health?.database === "ok"
                      ? "base de datos ok"
                      : "base de datos no disponible"
              }
              tone={databaseKey}
            />
          </div>
        </div>
      </section>
    </div>
  );
}