import { useCallback } from "react";

import { useWizard } from "../state/useWizard";
import { NarrativeField } from "../components/NarrativeField";

export function Step02CurrentNeed() {
  const { state, dispatch } = useWizard();
  const editable = state.estado === null || state.estado === "BORRADOR";

  const handleChange = useCallback(
    (value: string) => {
      dispatch({ type: "SET_NARRATIVE_FIELD", field: "necesidad_actual", value });
      dispatch({ type: "MARK_DIRTY", dirty: true });
    },
    [dispatch],
  );

  return (
    <div className="space-y-4">
      {!editable && (
        <p className="rounded border border-warning/40 bg-warning/10 px-4 py-2 text-sm text-warning">
          El requerimiento no esta en estado BORRADOR; la edicion esta deshabilitada.
        </p>
      )}
      <NarrativeField
        label="Necesidad actual"
        required
        rows={6}
        value={state.narrative.necesidad_actual}
        disabled={!editable}
        onChange={handleChange}
        hint="Describa la necesidad o problema que origina el requerimiento."
      />
    </div>
  );
}
