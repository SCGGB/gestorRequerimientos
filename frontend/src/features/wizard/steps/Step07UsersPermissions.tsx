import { useCallback } from "react";

import { useWizard } from "../state/useWizard";
import { NarrativeField } from "../components/NarrativeField";

export function Step07UsersPermissions() {
  const { state, dispatch } = useWizard();
  const editable = state.estado === null || state.estado === "BORRADOR";

  const handleChange = useCallback(
    (value: string) => {
      dispatch({ type: "SET_NARRATIVE_FIELD", field: "usuarios_permisos", value });
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
        label="Usuarios y permisos"
        required
        rows={6}
        value={state.narrative.usuarios_permisos}
        disabled={!editable}
        onChange={handleChange}
        hint="Usuarios autorizados, alcance de acceso y restricciones conocidas."
      />
    </div>
  );
}
