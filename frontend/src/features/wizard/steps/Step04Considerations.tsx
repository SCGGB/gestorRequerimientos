import { useWizard } from "../state/useWizard";
import { CollectionEditor } from "../components/CollectionEditor";

export function Step04Considerations() {
  const { state } = useWizard();

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-dark">
        Registre las consideraciones aplicables al requerimiento. Cada consideracion es un
        elemento independiente con orden y estado.
      </p>
      <CollectionEditor
        resource="consideraciones"
        items={state.collections.consideraciones}
        addLabel="Nueva consideracion"
      />
    </div>
  );
}
