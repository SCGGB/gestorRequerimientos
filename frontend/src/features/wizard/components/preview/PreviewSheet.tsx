import { useEffect, useRef, useState } from "react";

import type { PreviewDocument } from "../../../../api";
import { PreviewSection } from "./PreviewSection";
import { PreviewSignatures } from "./PreviewSignatures";
import { PreviewVersionTable } from "./PreviewVersionTable";

const SHEET_WIDTH = 816;
const MIN_SCALE = 0.4;

interface PreviewSheetProps {
  document: PreviewDocument;
}

export function PreviewSheet({ document }: PreviewSheetProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const element = containerRef.current;
    if (element === null) {
      return;
    }
    const updateScale = () => {
      const available = element.clientWidth;
      setScale(
        available >= SHEET_WIDTH
          ? 1
          : Math.max(available / SHEET_WIDTH, MIN_SCALE),
      );
    };
    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(element);
    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <div ref={containerRef} className="w-full overflow-x-auto">
      <div
        className="preview-sheet mx-auto bg-surface text-on-surface"
        style={{
          width: `${SHEET_WIDTH}px`,
          paddingTop: "2.5cm",
          paddingBottom: "2.5cm",
          paddingLeft: "2cm",
          paddingRight: "2cm",
          transform: `scale(${scale})`,
          transformOrigin: "top center",
        }}
      >
        <header className="mb-6 border-b border-border pb-4 text-center">
          <p className="text-xs uppercase tracking-wide text-neutral-dark">
            Especificacion de Requerimientos de Software
          </p>
          <h1 className="mt-1 text-lg font-semibold text-secondary">
            {document.titulo}
          </h1>
          <p className="mt-1 text-sm text-neutral-dark">
            {document.ticket} · Version {document.version_documento} ·{" "}
            {document.fecha_version}
          </p>
        </header>

        <div className="space-y-5">
          {document.secciones.map((section) => (
            <PreviewSection key={section.codigo} section={section} />
          ))}
        </div>

        <PreviewVersionTable rows={document.control_versiones} />
        <PreviewSignatures firmas={document.firmas} />
      </div>
    </div>
  );
}
