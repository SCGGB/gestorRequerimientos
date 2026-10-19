import { Badge } from "../../../components/ui/Badge";
import { useWizard } from "../state/useWizard";
import { WIZARD_STEPS, isComplete } from "../wizardSteps";
import type { WizardStepStatus } from "../state/types";

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

export function Step13Review() {
  const { state, dispatch } = useWizard();

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
    </div>
  );
}
