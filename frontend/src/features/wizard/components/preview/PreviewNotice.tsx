import { useEffect, useState } from "react";

export interface PreviewNoticeProps {
  dirty: boolean;
  onReload: () => void;
}

export function PreviewNotice({ dirty, onReload }: PreviewNoticeProps) {
  const [wasDirty, setWasDirty] = useState(false);
  const [showRefresh, setShowRefresh] = useState(false);

  useEffect(() => {
    if (dirty) {
      setWasDirty(true);
      setShowRefresh(false);
    } else if (wasDirty) {
      setShowRefresh(true);
    }
  }, [dirty, wasDirty]);

  if (dirty) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="mb-3 rounded-md border border-yellow-300 bg-yellow-50 px-4 py-2 text-sm text-yellow-900"
      >
        Hay cambios sin guardar. La vista previa se actualizará cuando se guarde
        automáticamente.
      </div>
    );
  }

  if (showRefresh) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="mb-3 flex items-center justify-between rounded-md border border-blue-300 bg-blue-50 px-4 py-2 text-sm text-blue-900"
      >
        <span>Hay una versión más reciente guardada. Actualizar vista previa.</span>
        <button
          type="button"
          onClick={() => {
            setShowRefresh(false);
            setWasDirty(false);
            onReload();
          }}
          className="ml-4 inline-flex items-center rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          Actualizar vista previa
        </button>
      </div>
    );
  }

  return null;
}
