import { useWizard } from "../state/useWizard";
import { CollectionEditor } from "../components/CollectionEditor";

export function Step03Objectives() {
  const { state } = useWizard();

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-dark">
        Defina los objetivos generales del requerimiento. Cada objetivo es un elemento
        independiente con orden y estado.
      </p>
      <CollectionEditor
        resource="objetivos"
        items={state.collections.objetivos}
        addLabel="Nuevo objetivo"
      />
    </div>
  );
}
