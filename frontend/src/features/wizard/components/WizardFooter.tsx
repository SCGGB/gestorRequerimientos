import { Button } from "../../../components/ui/Button";

interface WizardFooterProps {
  stepIndex: number;
  totalSteps: number;
  canGoBack: boolean;
  canGoForward: boolean;
  blockingReason: string | null;
  saving: boolean;
  dirty: boolean;
  onBack: () => void;
  onSave: () => void;
  onNext: () => void;
}

export function WizardFooter({
  stepIndex,
  totalSteps,
  canGoBack,
  canGoForward,
  blockingReason,
  saving,
  dirty,
  onBack,
  onSave,
  onNext,
}: WizardFooterProps) {
  const nextLabel = stepIndex === totalSteps - 1 ? "Revisar" : "Siguiente";

  return (
    <footer
      data-print-hide
      className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4"
    >
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="md" disabled={!canGoBack} onClick={onBack}>
          Anterior
        </Button>
        <Button
          variant="secondary"
          size="md"
          disabled={saving || !dirty}
          onClick={onSave}
        >
          {saving ? "Guardando..." : "Guardar borrador"}
        </Button>
      </div>
      <div className="flex flex-col items-end gap-1">
        {!canGoForward && blockingReason !== null && (
          <span className="text-xs text-danger" aria-live="polite">
            {blockingReason}
          </span>
        )}
        <Button size="md" disabled={!canGoForward || saving} onClick={onNext}>
          {nextLabel}
        </Button>
      </div>
    </footer>
  );
}
