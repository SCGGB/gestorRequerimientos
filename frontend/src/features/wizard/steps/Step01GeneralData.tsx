import { useCallback, useId, useMemo, useState } from "react";

import { createRequirement } from "../../../api";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { Select } from "../../../components/ui/Select";
import type { SelectOption } from "../../../components/ui/Select";
import { useChangeTypes } from "../../../hooks/useCatalogs";
import { toWizardError } from "../state/errors";
import { useWizard } from "../state/useWizard";
import type { WizardHeaderFields } from "../state/types";
import { WIZARD_STEPS, completionIssue, isComplete } from "../wizardSteps";

export function Step01GeneralData() {
  const { state, dispatch } = useWizard();
  const { header, requirementId, ticket, estado, error } = state;
  const { data: changeTypes, loading: catalogLoading, error: catalogError } = useChangeTypes();
  const [submitting, setSubmitting] = useState(false);
  const folioId = useId();

  const step = WIZARD_STEPS[0];
  const complete = useMemo(() => isComplete(state, step), [state, step]);
  const issue = complete ? null : completionIssue(state, step);
  const editable = estado === null || estado === "BORRADOR";
  const stepError = error !== null && error.stepIndex === 0 ? error.message : null;

  const update = useCallback(
    (field: keyof WizardHeaderFields, value: string | number | null) => {
      dispatch({ type: "SET_HEADER_FIELD", field, value });
      dispatch({ type: "MARK_DIRTY", dirty: true });
    },
    [dispatch],
  );

  const changeTypeOptions = useMemo<SelectOption[]>(
    () =>
      changeTypes
        .filter((changeType) => changeType.activo && changeType.id !== null)
        .map((changeType) => ({
          value: String(changeType.id),
          label: changeType.nombre,
        })),
    [changeTypes],
  );

  const handleCreate = useCallback(() => {
    if (requirementId !== null || !complete || !editable) {
      return;
    }
    setSubmitting(true);
    createRequirement({
      folio: Number(header.folio),
      titulo: header.titulo,
      tipo_cambio_id: header.tipo_cambio_id ?? 0,
      sistema: header.sistema,
      version_documento: header.version_documento,
      fecha_version: header.fecha_version,
    })
      .then((created) => {
        dispatch({ type: "LOAD_REQUIREMENT", requirement: created });
        dispatch({ type: "SET_STEP", stepIndex: 1 });
      })
      .catch((err: unknown) => {
        dispatch({ type: "SET_ERROR", error: toWizardError(err, 0) });
      })
      .finally(() => {
        setSubmitting(false);
      });
  }, [complete, dispatch, editable, header, requirementId]);

  return (
    <div className="space-y-4">
      {!editable && (
        <p className="rounded border border-warning/40 bg-warning/10 px-4 py-2 text-sm text-warning">
          El requerimiento no esta en estado BORRADOR; la edicion esta deshabilitada.
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1">
          <label htmlFor={folioId} className="text-sm font-semibold text-neutral-dark">
            Folio <span className="ml-1 text-danger">*</span>
          </label>
          <div className="flex items-stretch">
            <span className="flex h-10 items-center rounded-l border border-r-0 border-outline-variant bg-muted px-3 font-mono text-sm text-neutral-dark">
              T#
            </span>
            <input
              id={folioId}
              type="number"
              min={1}
              inputMode="numeric"
              value={header.folio}
              disabled={!editable || requirementId !== null}
              onChange={(event) => update("folio", event.target.value)}
              className="h-10 w-full rounded-r border border-outline-variant bg-surface px-3 text-sm text-secondary focus:outline-none focus:ring-[3px] focus:ring-primary/25 disabled:bg-muted"
            />
          </div>
          {requirementId !== null && ticket !== "" && (
            <span className="text-xs text-neutral-dark">Ticket: {ticket}</span>
          )}
        </div>

        <Input
          label="Titulo"
          required
          value={header.titulo}
          disabled={!editable}
          onChange={(event) => update("titulo", event.target.value)}
        />

        <Select
          label="Tipo de cambio"
          required
          placeholder={catalogLoading ? "Cargando..." : "Seleccione"}
          options={changeTypeOptions}
          value={header.tipo_cambio_id === null ? "" : String(header.tipo_cambio_id)}
          disabled={!editable || catalogLoading}
          hint={catalogError ?? undefined}
          onChange={(event) =>
            update(
              "tipo_cambio_id",
              event.target.value === "" ? null : Number(event.target.value),
            )
          }
        />

        <Input
          label="Sistema"
          required
          value={header.sistema}
          disabled={!editable}
          onChange={(event) => update("sistema", event.target.value)}
        />

        <Input
          label="Version documental"
          required
          value={header.version_documento}
          disabled={!editable}
          onChange={(event) => update("version_documento", event.target.value)}
        />

        <Input
          label="Fecha de version"
          type="date"
          required
          value={header.fecha_version}
          disabled={!editable}
          onChange={(event) => update("fecha_version", event.target.value)}
        />
      </div>

      {stepError !== null && (
        <p
          role="alert"
          className="rounded border border-danger/40 bg-danger/10 px-4 py-2 text-sm text-danger"
        >
          {stepError}
        </p>
      )}

      {requirementId === null && (
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={handleCreate} disabled={!complete || !editable || submitting}>
            {submitting ? "Creando..." : "Crear requerimiento"}
          </Button>
          {issue !== null && <span className="text-xs text-danger">{issue}</span>}
        </div>
      )}
    </div>
  );
}
