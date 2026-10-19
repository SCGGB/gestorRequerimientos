import { isApiError } from "@/api/client";

export interface PreviewErrorProps {
  error: unknown;
  onRetry: () => void;
}

function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    const status = error.status;
    const message = error.message || error.error?.message;

    if (status === 404) {
      return "No se encontró la vista previa para esta versión del requerimiento.";
    }

    if (message) {
      return message;
    }

    return `Error al cargar la vista previa (${status}).`;
  }

  if (error instanceof Error) {
    if (error.name === "AbortError") {
      return "La solicitud se canceló.";
    }
    return error.message || "Error al cargar la vista previa.";
  }

  return "Error al cargar la vista previa.";
}

export function PreviewError({ error, onRetry }: PreviewErrorProps) {
  const message = getErrorMessage(error);

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="mb-3 flex flex-col gap-2 rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900 sm:flex-row sm:items-center sm:justify-between"
    >
      <span>{message}</span>
      <button
        type="button"
        onClick={onRetry}
        className="inline-flex items-center justify-center rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
      >
        Reintentar
      </button>
    </div>
  );
}
