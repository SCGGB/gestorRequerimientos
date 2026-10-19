import { useWizard } from "../state/useWizard";
import { CollectionEditor } from "../components/CollectionEditor";

export function Step10Volumetry() {
  const { state } = useWizard();

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-dark">
        Capture los elementos de volumetria y rendimiento esperados. Cada elemento es
        independiente con orden y estado.
      </p>
      <CollectionEditor
        resource="volumetria"
        items={state.collections.volumetria}
        addLabel="Nuevo elemento de volumetria"
      />
    </div>
  );
}
