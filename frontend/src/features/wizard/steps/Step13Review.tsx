import { Badge } from "../../../components/ui/Badge";
import { usePreview } from "../../../hooks/usePreview";
import { useWizard } from "../state/useWizard";
import { WIZARD_STEPS, isComplete } from "../wizardSteps";
import type { WizardStepStatus } from "../state/types";
import { PreviewSheet } from "../components/preview/PreviewSheet";
import { PreviewNotice } from "../components/preview/PreviewNotice";
import { PreviewError } from "../components/preview/PreviewError";

const STATUS_TONE: Record<WizardStepStatus, "success" | "info" | "danger" | "neutral"> = {
  completado: "success",
  activo: "info",
  error: "danger",
  pendiente: "neutral",
};

const STATUS_LABEL: Record<WizardStepStatus, string> = {
  completado: "Completado",
  activo: "En curso",
  error: "Error",
  pendiente: "Pendiente",
};

export interface Step13ReviewProps {
  dirty: boolean;
}

export function Step13Review({ dirty }: Step13ReviewProps) {
  const { state, dispatch } = useWizard();
  const preview = usePreview(state.requirementId, state.versionId);

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-dark">
        Revision del estado de cada paso. La vista previa y la generacion de documentos
        se realizan al finalizar la captura.
      </p>

      <ul className="rounded border border-border bg-surface">
        {WIZARD_STEPS.map((step, index) => {
          const status = state.stepStatus[index] ?? (isComplete(state, step) ? "completado" : "pendiente");
          return (
            <li
              key={step.id}
              className="flex items-center justify-between gap-3 border-t border-border px-4 py-3 first:border-t-0"
            >
              <div>
                <p className="text-sm font-semibold text-secondary">
                  Paso {step.numero}: {step.titulo}
                </p>
                <p className="text-xs text-neutral-dark">
                  Obligatorios: {step.obligatorios.length > 0 ? step.obligatorios.join(", ") : "ninguno"}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge label={STATUS_LABEL[status]} tone={STATUS_TONE[status]} />
                {index !== state.stepIndex && (
                  <button
                    type="button"
                    className="text-xs font-semibold text-primary underline-offset-2 hover:underline"
                    onClick={() => dispatch({ type: "SET_STEP", stepIndex: index })}
                  >
                    Ir al paso
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      {state.ticket !== "" && (
        <p className="text-sm text-neutral-dark">
          Ticket: <span className="font-semibold text-secondary">{state.ticket}</span>
        </p>
      )}

      <section className="space-y-3" aria-label="Vista previa del requerimiento">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-base font-semibold text-secondary">Vista previa</h3>
          {preview.data !== null && (
            <button
              type="button"
              className="preview-actions inline-flex items-center rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-secondary hover:bg-muted"
              onClick={() => window.print()}
            >
              Imprimir
            </button>
          )}
        </div>
        <PreviewNotice dirty={dirty} onReload={preview.reload} />
        {preview.error !== null && (
          <PreviewError error={preview.error} onRetry={preview.reload} />
        )}
        {preview.loading && preview.data === null && (
          <p role="status" className="text-sm text-neutral-dark">
            Cargando vista previa...
          </p>
        )}
        {preview.data !== null && <PreviewSheet document={preview.data} />}
      </section>
    </div>
  );
}
