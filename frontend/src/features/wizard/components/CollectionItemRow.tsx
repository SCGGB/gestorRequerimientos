import type { CollectionItemResponse } from "../../../api";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";

interface CollectionItemRowProps {
  item: CollectionItemResponse;
  editing: boolean;
  editingContent: string;
  disabled: boolean;
  isFirst: boolean;
  isLast: boolean;
  onStartEdit: () => void;
  onChangeEdit: (value: string) => void;
  onSave: () => void;
  onCancel: () => void;
  onDelete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
}

export function CollectionItemRow({
  item,
  editing,
  editingContent,
  disabled,
  isFirst,
  isLast,
  onStartEdit,
  onChangeEdit,
  onSave,
  onCancel,
  onDelete,
  onMoveUp,
  onMoveDown,
}: CollectionItemRowProps) {
  if (editing) {
    return (
      <li className="flex items-start gap-2 border-t border-border px-3 py-2 first:border-t-0">
        <div className="flex-1">
          <Input
            label={`Editar elemento #${item.orden}`}
            value={editingContent}
            disabled={disabled}
            onChange={(event) => onChangeEdit(event.target.value)}
          />
        </div>
        <div className="mt-6 flex items-center gap-2">
          <Button size="sm" disabled={disabled || editingContent.trim() === ""} onClick={onSave}>
            Guardar
          </Button>
          <Button size="sm" variant="secondary" disabled={disabled} onClick={onCancel}>
            Cancelar
          </Button>
        </div>
      </li>
    );
  }

  return (
    <li className="flex items-start gap-3 border-t border-border px-3 py-2 first:border-t-0">
      <span className="mt-2 font-mono text-xs text-neutral-dark">#{item.orden}</span>
      <p className="flex-1 py-2 text-sm text-secondary">{item.contenido}</p>
      <div className="flex items-center gap-1">
        <Button
          size="sm"
          variant="ghost"
          aria-label="Subir"
          disabled={disabled || isFirst}
          onClick={onMoveUp}
        >
          &uarr;
        </Button>
        <Button
          size="sm"
          variant="ghost"
          aria-label="Bajar"
          disabled={disabled || isLast}
          onClick={onMoveDown}
        >
          &darr;
        </Button>
        <Button size="sm" variant="secondary" disabled={disabled} onClick={onStartEdit}>
          Editar
        </Button>
        <Button size="sm" variant="danger" disabled={disabled} onClick={onDelete}>
          Eliminar
        </Button>
      </div>
    </li>
  );
}
