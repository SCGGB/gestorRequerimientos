import {
  REQUIREMENT_STATUS_LABELS,
  REQUIREMENT_STATUS_TONES,
} from "../../api";
import type { RequirementStatus } from "../../api";
import { Button } from "../../components/ui/Button";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Select } from "../../components/ui/Select";
import type { SelectOption } from "../../components/ui/Select";
import { Input } from "../../components/ui/Input";
import { useNav } from "../../navigation/NavContext";
import { useRequirementsList } from "./useRequirementsList";

const statusOptions: SelectOption[] = (
  Object.keys(REQUIREMENT_STATUS_LABELS) as RequirementStatus[]
).map((status) => ({
  value: status,
  label: REQUIREMENT_STATUS_LABELS[status],
}));

export function RequirementsListPage() {
  const { navigate } = useNav();
  const {
    data,
    loading,
    error,
    page,
    size,
    totalPages,
    estado,
    folioInput,
    folioError,
    setEstado,
    setFolioInput,
    applyFolioFilter,
    goToPage,
  } = useRequirementsList();

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const rangeStart = total === 0 ? 0 : (page - 1) * size + 1;
  const rangeEnd = Math.min(page * size, total);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-secondary">Requerimientos</h1>
          <p className="mt-1 text-sm text-neutral-dark">
            Listado de requerimientos registrados.
          </p>
        </div>
        <Button
          onClick={() => navigate({ name: "wizard" }, "new-requirement")}
        >
          Nuevo
        </Button>
      </div>

      <section className="rounded-lg border border-border bg-surface p-4">
        <form
          className="flex flex-wrap items-end gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            applyFolioFilter();
          }}
        >
          <div className="w-56">
            <Select
              label="Estado"
              placeholder="Todos los estados"
              options={statusOptions}
              value={estado}
              onChange={(event) =>
                setEstado(event.target.value as RequirementStatus | "")
              }
            />
          </div>
          <div className="w-40">
            <Input
              label="Folio"
              type="number"
              min={1}
              inputMode="numeric"
              value={folioInput}
              error={folioError}
              onChange={(event) => setFolioInput(event.target.value)}
            />
          </div>
          <Button type="submit" variant="secondary">
            Filtrar
          </Button>
        </form>
      </section>

      {error !== null && (
        <p
          role="alert"
          className="rounded border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger"
        >
          {error.message}
        </p>
      )}

      <section className="overflow-hidden rounded-lg border border-border bg-surface">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-muted text-left text-[11px] font-bold uppercase tracking-[0.05em] text-neutral-dark">
              <th scope="col" className="px-4 py-3">
                Ticket
              </th>
              <th scope="col" className="px-4 py-3">
                Titulo
              </th>
              <th scope="col" className="px-4 py-3">
                Estado
              </th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-center text-neutral-dark">
                  Cargando requerimientos...
                </td>
              </tr>
            )}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-center text-neutral-dark">
                  No hay requerimientos para los filtros aplicados.
                </td>
              </tr>
            )}
            {!loading &&
              items.map((item) => (
                <tr key={item.id} className="border-t border-border">
                  <td className="px-4 py-3 font-mono text-secondary">
                    {item.ticket}
                  </td>
                  <td className="px-4 py-3 text-secondary">{item.titulo}</td>
                  <td className="px-4 py-3">
                    <StatusBadge
                      label={REQUIREMENT_STATUS_LABELS[item.estado]}
                      tone={REQUIREMENT_STATUS_TONES[item.estado]}
                    />
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-neutral-dark">
          Mostrando {rangeStart}-{rangeEnd} de {total}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1 || loading}
            onClick={() => goToPage(page - 1)}
          >
            Anterior
          </Button>
          <span className="text-xs text-neutral-dark">
            Pagina {page} de {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= totalPages || loading}
            onClick={() => goToPage(page + 1)}
          >
            Siguiente
          </Button>
        </div>
      </div>
    </div>
  );
}
