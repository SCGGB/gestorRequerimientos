import { useWizard } from "../state/useWizard";
import { CollectionEditor } from "../components/CollectionEditor";

export function Step08Restrictions() {
  const { state } = useWizard();

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-dark">
        Detalle las restricciones del requerimiento. Cada restriccion es un elemento
        independiente con orden y estado.
      </p>
      <CollectionEditor
        resource="restricciones"
        items={state.collections.restricciones}
        addLabel="Nueva restriccion"
      />
    </div>
  );
}
