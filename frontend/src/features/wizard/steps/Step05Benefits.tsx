import { BENEFIT_KIND_LABELS } from "../../../api";
import type { BenefitKind } from "../../../api";
import { CollectionEditor } from "../components/CollectionEditor";
import { useWizard } from "../state/useWizard";

const KINDS: readonly BenefitKind[] = ["CUALITATIVO", "CUANTITATIVO"];

export function Step05Benefits() {
  const { state } = useWizard();

  return (
    <div className="space-y-6">
      <p className="text-sm text-neutral-dark">
        Registre los beneficios esperados en dos secciones independientes. Cada beneficio
        conserva su tipo (cualitativo o cuantitativo).
      </p>
      {KINDS.map((kind) => (
        <section key={kind} className="space-y-3">
          <h3 className="text-sm font-semibold text-secondary">
            Beneficios {BENEFIT_KIND_LABELS[kind].toLowerCase()}
          </h3>
          <CollectionEditor
            resource="beneficios"
            kind={kind}
            items={state.collections.beneficios}
            addLabel={`Nuevo beneficio ${BENEFIT_KIND_LABELS[kind].toLowerCase()}`}
          />
        </section>
      ))}
    </div>
  );
}
