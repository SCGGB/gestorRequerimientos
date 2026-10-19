import { useCallback } from "react";

import { SIGNATURE_ROLE_LABELS } from "../../../api";
import type { SignatureRole } from "../../../api";
import { Input } from "../../../components/ui/Input";
import { Select } from "../../../components/ui/Select";
import { usePositions } from "../../../hooks/useCatalogs";
import { useWizard } from "../state/useWizard";

const ROLES: readonly SignatureRole[] = ["ELABORO", "REVISO", "AUTORIZO"];

function SignerSection({ role }: { role: SignatureRole }) {
  const { state, dispatch } = useWizard();
  const signer = state.signers[role];
  const editable = state.estado === null || state.estado === "BORRADOR";
  const catalog = usePositions(role);

  const handleNameChange = useCallback(
    (value: string) => {
      dispatch({ type: "SET_SIGNER_FIELD", role, field: "nombre", value });
      dispatch({ type: "MARK_DIRTY", dirty: true });
    },
    [dispatch, role],
  );

  const handleCargoChange = useCallback(
    (value: string) => {
      const cargoId = value === "" ? null : Number(value);
      const cargo = catalog.data.find((position) => position.id === cargoId)?.nombre ?? "";
      dispatch({ type: "SET_SIGNER_FIELD", role, field: "cargo_id", value: cargoId });
      dispatch({ type: "SET_SIGNER_FIELD", role, field: "cargo", value: cargo });
      dispatch({ type: "MARK_DIRTY", dirty: true });
    },
    [catalog.data, dispatch, role],
  );

  return (
    <section className="space-y-3 rounded border border-border bg-surface p-4">
      <h3 className="text-sm font-semibold text-secondary">{SIGNATURE_ROLE_LABELS[role]}</h3>
      {catalog.error !== null && (
        <p className="text-xs text-danger">No se pudo cargar el catalogo de cargos.</p>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        <Input
          label="Nombre"
          required={role !== "REVISO"}
          value={signer.nombre}
          disabled={!editable}
          onChange={(event) => handleNameChange(event.target.value)}
        />
        <Select
          label="Cargo"
          value={signer.cargo_id === null ? "" : String(signer.cargo_id)}
          disabled={!editable || catalog.loading}
          placeholder={catalog.loading ? "Cargando cargos..." : "Seleccione un cargo"}
          options={catalog.data
            .filter((position) => position.activo)
            .map((position) => ({ value: String(position.id), label: position.nombre }))}
          onChange={(event) => handleCargoChange(event.target.value)}
        />
      </div>
    </section>
  );
}

export function Step12DocumentControl() {
  const { state } = useWizard();
  const editable = state.estado === null || state.estado === "BORRADOR";

  return (
    <div className="space-y-4">
      {!editable && (
        <p className="rounded border border-warning/40 bg-warning/10 px-4 py-2 text-sm text-warning">
          El requerimiento no esta en estado BORRADOR; la edicion esta deshabilitada.
        </p>
      )}
      <p className="text-sm text-neutral-dark">
        Capture el nombre y cargo de quien elaboro, reviso y autorizo. Este paso es de
        captura; el registro de firmas se realiza fuera del wizard.
      </p>
      {ROLES.map((role) => (
        <SignerSection key={role} role={role} />
      ))}
    </div>
  );
}
