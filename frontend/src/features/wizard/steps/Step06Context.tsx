import { useCallback } from "react";

import { useWizard } from "../state/useWizard";
import { NarrativeField } from "../components/NarrativeField";

export function Step06Context() {
  const { state, dispatch } = useWizard();
  const editable = state.estado === null || state.estado === "BORRADOR";

  const handleChange = useCallback(
    (field: "contexto_descripcion" | "contexto_manejo_errores") => (value: string) => {
      dispatch({ type: "SET_NARRATIVE_FIELD", field, value });
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
        label="Descripcion contextual"
        required
        rows={6}
        value={state.narrative.contexto_descripcion}
        disabled={!editable}
        onChange={handleChange("contexto_descripcion")}
        hint="Contexto del sistema, alcance y condiciones relevantes."
      />
      <NarrativeField
        label="Manejo de errores"
        rows={4}
        value={state.narrative.contexto_manejo_errores}
        disabled={!editable}
        onChange={handleChange("contexto_manejo_errores")}
        hint="Opcional. Comportamiento ante errores o excepciones."
      />
      <p className="text-xs text-neutral-dark">
        Este paso no ofrece carga de imagenes ni anexos en esta version.
      </p>
    </div>
  );
}
