import { useWizard } from "../state/useWizard";
import { CollectionEditor } from "../components/CollectionEditor";

export function Step11Risks() {
  const { state } = useWizard();

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-dark">
        Liste los riesgos iniciales identificados. Cada riesgo es un elemento independiente
        con orden y estado.
      </p>
      <CollectionEditor
        resource="riesgos"
        items={state.collections.riesgos}
        addLabel="Nuevo riesgo"
      />
    </div>
  );
}
