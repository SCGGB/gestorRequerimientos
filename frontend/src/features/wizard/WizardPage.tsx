import { useCallback, useEffect, useMemo } from "react";
import type { ReactNode } from "react";

import { ApiError } from "../../api";
import type { VersionUpdatePayload } from "../../api";
import { useAutosave } from "../../hooks/useAutosave";
import { useNav } from "../../navigation/NavContext";
import { WIZARD_STEPS, completionIssue, isComplete } from "./wizardSteps";
import { useWizard } from "./state/useWizard";
import type { WizardHeaderFields, WizardNarrativeFields } from "./state/types";
import { WizardStepper } from "./components/WizardStepper";
import { WizardFooter } from "./components/WizardFooter";
import { Step01GeneralData } from "./steps/Step01GeneralData";
import { Step02CurrentNeed } from "./steps/Step02CurrentNeed";
import { Step03Objectives } from "./steps/Step03Objectives";
import { Step04Considerations } from "./steps/Step04Considerations";
import { Step05Benefits } from "./steps/Step05Benefits";
import { Step06Context } from "./steps/Step06Context";
import { Step07UsersPermissions } from "./steps/Step07UsersPermissions";
import { Step08Restrictions } from "./steps/Step08Restrictions";
import { Step09FutureRequirements } from "./steps/Step09FutureRequirements";
import { Step10Volumetry } from "./steps/Step10Volumetry";
import { Step11Risks } from "./steps/Step11Risks";
import { Step12DocumentControl } from "./steps/Step12DocumentControl";
import { Step13Review } from "./steps/Step13Review";

function buildVersionPayload(
  header: WizardHeaderFields,
  narrative: WizardNarrativeFields,
): VersionUpdatePayload {
  return {
    titulo: header.titulo,
    tipo_cambio_id: header.tipo_cambio_id ?? undefined,
    sistema: header.sistema,
    version_documento: header.version_documento,
    fecha_version: header.fecha_version,
    necesidad_actual: narrative.necesidad_actual,
    contexto_descripcion: narrative.contexto_descripcion,
    contexto_manejo_errores: narrative.contexto_manejo_errores,
    usuarios_permisos: narrative.usuarios_permisos,
    requisitos_futuros_aplica: narrative.requisitos_futuros_aplica,
    requisitos_futuros_texto: narrative.requisitos_futuros_texto,
  };
}

function renderStep(stepIndex: number): ReactNode {
  switch (stepIndex) {
    case 0:
      return <Step01GeneralData />;
    case 1:
      return <Step02CurrentNeed />;
    case 2:
      return <Step03Objectives />;
    case 3:
      return <Step04Considerations />;
    case 4:
      return <Step05Benefits />;
    case 5:
      return <Step06Context />;
    case 6:
      return <Step07UsersPermissions />;
    case 7:
      return <Step08Restrictions />;
    case 8:
      return <Step09FutureRequirements />;
    case 9:
      return <Step10Volumetry />;
    case 10:
      return <Step11Risks />;
    case 11:
      return <Step12DocumentControl />;
    case 12:
      return <Step13Review />;
  }
}

export function WizardPage() {
  const { navigate } = useNav();
  const { state, dispatch } = useWizard();
  const { stepIndex, stepStatus, dirty, error, requirementId, versionId } = state;

  const autosave = useAutosave({
    requirementId,
    versionId,
    onSaved: (version) => dispatch({ type: "REFRESH_VERSION", version }),
    onError: (err) => {
      dispatch({
        type: "SET_ERROR",
        error:
          err instanceof ApiError
            ? { code: err.code, message: err.message, details: err.details }
            : {
                code: "save_error",
                message: "No se pudo guardar el borrador.",
                details: null,
              },
      });
    },
  });

  const versionPayload = useMemo(
    () => buildVersionPayload(state.header, state.narrative),
    [state.header, state.narrative],
  );

  useEffect(() => {
    if (!dirty || requirementId === null || versionId === null) {
      return;
    }
    autosave.schedule(versionPayload);
  }, [dirty, requirementId, versionId, versionPayload, autosave.schedule]);

  const step = WIZARD_STEPS[stepIndex];
  const stepComplete = useMemo(() => (step ? isComplete(state, step) : false), [state, step]);
  const issue = useMemo(() => (step ? completionIssue(state, step) : null), [state, step]);

  const requiresCreation = stepIndex === 0 && requirementId === null;
  const canGoBack = stepIndex > 0;
  const canGoForward = stepComplete && !requiresCreation;
  const blockingReason = canGoForward
    ? null
    : requiresCreation
      ? "Cree el requerimiento para continuar."
      : issue;

  const handleBack = useCallback(() => {
    if (canGoBack) {
      dispatch({ type: "SET_STEP", stepIndex: stepIndex - 1 });
    }
  }, [canGoBack, dispatch, stepIndex]);

  const handleSave = useCallback(() => {
    if (requirementId === null || versionId === null) {
      dispatch({ type: "MARK_DIRTY", dirty: false });
      return;
    }
    void autosave.saveNow(versionPayload);
  }, [autosave, dispatch, requirementId, versionId, versionPayload]);

  const handleNext = useCallback(() => {
    if (!canGoForward) {
      return;
    }
    if (stepIndex < WIZARD_STEPS.length - 1) {
      dispatch({ type: "SET_STEP", stepIndex: stepIndex + 1 });
    } else {
      navigate({ name: "list" }, "requirements");
    }
  }, [canGoForward, dispatch, navigate, stepIndex]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-secondary">Nuevo Requerimiento</h1>
        <p className="mt-1 text-sm text-neutral-dark">
          Captura escalonada segun las secciones del machote institucional.
        </p>
      </div>

      <section className="grid gap-6 rounded-lg border border-border bg-surface p-6 lg:grid-cols-[240px_1fr]">
        <aside className="border-b border-border pb-6 lg:border-b-0 lg:border-r lg:pr-6">
          <WizardStepper steps={WIZARD_STEPS} stepStatus={stepStatus} stepIndex={stepIndex} />
        </aside>
        <div className="flex flex-col">
          <header className="mb-4">
            <h2 className="text-lg font-semibold text-secondary">
              Paso {step.numero}: {step.titulo}
            </h2>
          </header>
          <div className="flex-1">
            {renderStep(stepIndex)}
            {error !== null && error.stepIndex !== stepIndex && (
              <p
                role="alert"
                className="mt-4 rounded border border-danger/40 bg-danger/10 px-4 py-2 text-sm text-danger"
              >
                {error.message}
              </p>
            )}
          </div>
          <WizardFooter
            stepIndex={stepIndex}
            totalSteps={WIZARD_STEPS.length}
            canGoBack={canGoBack}
            canGoForward={canGoForward}
            blockingReason={blockingReason}
            saving={autosave.saving}
            dirty={requirementId !== null && autosave.dirty}
            onBack={handleBack}
            onSave={handleSave}
            onNext={handleNext}
          />
        </div>
      </section>
    </div>
  );
}
