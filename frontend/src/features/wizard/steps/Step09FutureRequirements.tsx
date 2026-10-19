import { useCallback } from "react";

import { CollectionEditor } from "../components/CollectionEditor";
import { NarrativeField } from "../components/NarrativeField";
import { useWizard } from "../state/useWizard";

export function Step09FutureRequirements() {
  const { state, dispatch } = useWizard();
  const { narrative, collections } = state;
  const editable = state.estado === null || state.estado === "BORRADOR";
  const aplica = narrative.requisitos_futuros_aplica;

  const handleToggle = useCallback(
    (checked: boolean) => {
      dispatch({ type: "SET_NARRATIVE_FIELD", field: "requisitos_futuros_aplica", value: checked });
      dispatch({ type: "MARK_DIRTY", dirty: true });
    },
    [dispatch],
  );

  const handleTextChange = useCallback(
    (value: string) => {
      dispatch({ type: "SET_NARRATIVE_FIELD", field: "requisitos_futuros_texto", value });
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

      <label className="flex items-center gap-2 text-sm text-secondary">
        <input
          type="checkbox"
          checked={!aplica}
          disabled={!editable}
          onChange={(event) => handleToggle(!event.target.checked)}
        />
        No aplica (sin requisitos futuros)
      </label>

      {aplica && (
        <>
          <NarrativeField
            label="Descripcion de requisitos futuros"
            rows={4}
            value={narrative.requisitos_futuros_texto}
            disabled={!editable}
            onChange={handleTextChange}
            hint="Opcional: describa los requisitos futuros en bloque o registre elementos individuales abajo."
          />
          <CollectionEditor
            resource="requisitos-futuros"
            items={collections["requisitos-futuros"]}
            addLabel="Nuevo requisito futuro"
          />
        </>
      )}
    </div>
  );
}
