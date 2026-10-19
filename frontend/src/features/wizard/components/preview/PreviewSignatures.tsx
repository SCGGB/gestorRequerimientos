import type { PreviewFirmas, PreviewSigner } from "../../../../api";

const EMPTY_VALUE = "—";

function signerValue(signer: PreviewSigner | null): string {
  if (signer === null) {
    return EMPTY_VALUE;
  }
  if (signer.cargo === null || signer.cargo === "") {
    return signer.nombre;
  }
  return `${signer.nombre}\n${signer.cargo}`;
}

interface PreviewSignaturesProps {
  firmas: PreviewFirmas;
}

export function PreviewSignatures({ firmas }: PreviewSignaturesProps) {
  const columns: { titulo: string; valor: string }[] = [
    { titulo: "Elaboro", valor: signerValue(firmas.elaboro) },
    { titulo: "Reviso", valor: signerValue(firmas.reviso) },
    { titulo: "Autorizo", valor: signerValue(firmas.autorizo) },
  ];

  return (
    <section className="mt-8 space-y-2">
      <h2 className="text-sm font-semibold text-secondary">Firmas</h2>
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="border-b border-border text-left text-neutral-dark">
            {columns.map((column) => (
              <th key={column.titulo} className="py-2 pr-3 font-semibold">
                {column.titulo}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            {columns.map((column) => (
              <td key={column.titulo} className="whitespace-pre-line py-4 pr-3">
                {column.valor}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </section>
  );
}
