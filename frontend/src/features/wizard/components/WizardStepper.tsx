import type { WizardStepDefinition } from "../wizardSteps";
import type { WizardStepStatus } from "../state/types";

interface StepperItemProps {
  step: WizardStepDefinition;
  index: number;
  status: WizardStepStatus;
  isActive: boolean;
}

function StepperItem({ step, index, status, isActive }: StepperItemProps) {
  const statusText = status === "error" ? "Error" : status;
  const isCompleted = status === "completado";
  const isError = status === "error";
  const circleClasses = `flex h-9 w-9 items-center justify-center rounded-full border text-sm font-semibold ${
    isActive || isError
      ? "border-primary bg-primary text-on-primary"
      : isCompleted
        ? "border-primary bg-primary/10 text-primary"
        : "border-outline-variant bg-surface text-neutral-dark"
  }`;
  const textClasses = `mt-2 text-xs font-semibold ${
    isActive ? "text-secondary" : isCompleted || isError ? "text-primary" : "text-neutral-dark"
  }`;
  const lineClasses = index === 0 ? "hidden" : "absolute -left-10 top-4 h-px w-10 bg-border";

  return (
    <li className="relative flex flex-col items-center text-center" aria-current={isActive ? "step" : undefined}>
      <div className="relative">
        <span className={lineClasses} aria-hidden="true" />
        <span className={circleClasses}>{step.numero}</span>
      </div>
      <span className={textClasses}>{step.titulo}</span>
      <span className="mt-1 text-[11px] uppercase tracking-[0.05em] text-neutral-dark">{statusText}</span>
    </li>
  );
}

interface WizardStepperProps {
  steps: readonly WizardStepDefinition[];
  stepStatus: WizardStepStatus[];
  stepIndex: number;
}

export function WizardStepper({ steps, stepStatus, stepIndex }: WizardStepperProps) {
  return (
    <nav aria-label="Pasos del wizard" className="w-full">
      <ol className="flex flex-row flex-wrap items-start justify-center gap-8 md:flex-col md:items-start md:gap-10">
        {steps.map((step, index) => (
          <StepperItem
            key={step.id}
            step={step}
            index={index}
            status={stepStatus[index] ?? "pendiente"}
            isActive={index === stepIndex}
          />
        ))}
      </ol>
    </nav>
  );
}
