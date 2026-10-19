import type {
  PreviewBlock,
  PreviewSection as PreviewSectionData,
} from "../../../../api";

interface PreviewSectionProps {
  section: PreviewSectionData;
}

function BlockView({ block }: { block: PreviewBlock }) {
  if (block.tipo === "lista" && block.items !== null) {
    return (
      <ul className="list-disc space-y-1 pl-6 text-sm">
        {block.items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    );
  }
  return (
    <p className="whitespace-pre-line text-sm">{block.texto ?? ""}</p>
  );
}

export function PreviewSection({ section }: PreviewSectionProps) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold text-secondary">
        {section.numero !== "" ? `${section.numero}. ` : ""}
        {section.titulo}
      </h2>
      {section.bloques.map((block, index) => (
        <BlockView key={index} block={block} />
      ))}
    </section>
  );
}
