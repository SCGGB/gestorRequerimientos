import { useState } from "react";

import { ApiError } from "../../../../api";
import type { RequirementStatus } from "../../../../api";
import { useAuth } from "../../../../auth/AuthContext";
import { Button } from "../../../../components/ui/Button";

const GENERATABLE_STATUSES: RequirementStatus[] = ["APROBADO", "GENERADO"];

function disabledReason(
  status: RequirementStatus | null,
  canGenerate: boolean,
): string | null {
  if (!canGenerate) {
    return "Su rol no permite generar documentos (requiere Autorizo o Administrador).";
  }
  if (status === null) {
    return "Guarde el requerimiento para generar documentos.";
  }
  if (GENERATABLE_STATUSES.includes(status)) {
    return null;
  }
  return "La generacion solo esta disponible cuando el requerimiento esta APROBADO.";
}

function errorMessage(error: Error | null): string | null {
  if (error === null) {
    return null;
  }
  if (error instanceof ApiError && error.code === "forbidden") {
    return "No tiene permiso para generar documentos.";
  }
  return error.message;
}

export interface DocumentActionsProps {
  status: RequirementStatus | null;
  loading: boolean;
  error: Error | null;
  onGenerate: () => Promise<boolean>;
}

export function DocumentActions({
  status,
  loading,
  error,
  onGenerate,
}: DocumentActionsProps) {
  const { hasRole } = useAuth();
  const [message, setMessage] = useState<string | null>(null);
  const canGenerate = hasRole("AUTORIZO") || hasRole("ADMIN");
  const reason = disabledReason(status, canGenerate);
  const errorText = errorMessage(error);

  const handleGenerate = async () => {
    setMessage(null);
    if (await onGenerate()) {
      setMessage("Documentos DOCX y PDF generados correctamente.");
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        <Button
          onClick={() => {
            void handleGenerate();
          }}
          disabled={loading || reason !== null}
        >
          {loading ? "Generando..." : "Generar DOCX/PDF"}
        </Button>
        {reason !== null && (
          <p className="text-xs text-neutral-dark">{reason}</p>
        )}
      </div>
      {errorText !== null && (
        <p
          role="alert"
          className="rounded border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger"
        >
          {errorText}
        </p>
      )}
      {message !== null && (
        <p role="status" className="text-sm text-success">
          {message}
        </p>
      )}
    </div>
  );
}
