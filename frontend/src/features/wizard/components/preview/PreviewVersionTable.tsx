import type { PreviewVersionRow } from "../../../../api";

const EMPTY_VALUE = "—";

function cellValue(value: string | null): string {
  return value === null || value === "" ? EMPTY_VALUE : value;
}

interface PreviewVersionTableProps {
  rows: PreviewVersionRow[];
}

export function PreviewVersionTable({ rows }: PreviewVersionTableProps) {
  return (
    <section className="mt-8 space-y-2">
      <h2 className="text-sm font-semibold text-secondary">
        Control de versiones
      </h2>
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="border-b border-border text-left text-neutral-dark">
            <th className="py-2 pr-3 font-semibold">Version</th>
            <th className="py-2 pr-3 font-semibold">Fecha</th>
            <th className="py-2 pr-3 font-semibold">Descripcion del cambio</th>
            <th className="py-2 pr-3 font-semibold">Reviso</th>
            <th className="py-2 font-semibold">Elaboro</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.version} className="border-b border-border">
              <td className="py-2 pr-3">{row.version}</td>
              <td className="py-2 pr-3">{row.fecha}</td>
              <td className="py-2 pr-3">{cellValue(row.descripcion_cambio)}</td>
              <td className="py-2 pr-3">{cellValue(row.reviso)}</td>
              <td className="py-2">{cellValue(row.elaboro)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
