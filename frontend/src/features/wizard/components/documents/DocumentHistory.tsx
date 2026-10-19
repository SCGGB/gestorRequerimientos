import type { GeneratedDocument } from "../../../../api";
import { Badge } from "../../../../components/ui/Badge";
import { Button } from "../../../../components/ui/Button";

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("es-MX", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function formatSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${(bytes / 1024).toFixed(1)} kB`;
}

export interface DocumentHistoryProps {
  documents: GeneratedDocument[];
  loading: boolean;
  onDownload: (documentId: number) => void;
}

export function DocumentHistory({
  documents,
  loading,
  onDownload,
}: DocumentHistoryProps) {
  return (
    <section aria-label="Documentos generados" className="space-y-2">
      <h4 className="text-sm font-semibold text-secondary">Historico</h4>
      {loading && documents.length === 0 ? (
        <p role="status" className="text-sm text-neutral-dark">
          Cargando documentos...
        </p>
      ) : documents.length === 0 ? (
        <p className="text-sm text-neutral-dark">
          Aun no hay documentos generados.
        </p>
      ) : (
        <ul className="divide-y divide-border rounded border border-border bg-surface">
          {documents.map((document) => (
            <li
              key={document.id}
              className="flex flex-wrap items-center justify-between gap-3 px-4 py-2"
            >
              <div className="flex flex-wrap items-center gap-2 text-sm text-secondary">
                <Badge label={document.formato} tone="info" />
                <span className="font-medium">{document.nombre_archivo}</span>
                <span className="text-xs text-neutral-dark">
                  {formatDate(document.generado_at)} ·{" "}
                  {formatSize(document.tamano_bytes)}
                </span>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onDownload(document.id)}
              >
                Descargar
              </Button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
