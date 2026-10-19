import { useCallback, useMemo, useState } from "react";

import {
  addCollectionItem,
  deleteCollectionItem,
  getVersion,
  reorderCollectionItems,
  updateCollectionItem,
} from "../../../api";
import type {
  BenefitKind,
  BenefitResponse,
  CollectionItemResponse,
  CollectionResource,
  VersionResponse,
} from "../../../api";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { toWizardError } from "../state/errors";
import { useWizard } from "../state/useWizard";
import { CollectionItemRow } from "./CollectionItemRow";

interface CollectionEditorProps {
  resource: CollectionResource;
  items: CollectionItemResponse[];
  kind?: BenefitKind;
  addLabel?: string;
}

function benefitKindOf(item: CollectionItemResponse): BenefitKind | undefined {
  return "tipo" in item ? (item as BenefitResponse).tipo : undefined;
}

export function CollectionEditor({ resource, items, kind, addLabel }: CollectionEditorProps) {
  const { state, dispatch } = useWizard();
  const { requirementId, versionId, estado } = state;
  const editable = estado === null || estado === "BORRADOR";

  const [newContent, setNewContent] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState("");
  const [busy, setBusy] = useState(false);

  const activeItems = useMemo(
    () => items.filter((item) => item.activo !== false && item.id !== null),
    [items],
  );

  const visible = useMemo(
    () => (kind === undefined ? activeItems : activeItems.filter((item) => benefitKindOf(item) === kind)),
    [activeItems, kind],
  );

  const reportError = useCallback(
    (err: unknown) => {
      dispatch({ type: "SET_ERROR", error: toWizardError(err) });
    },
    [dispatch],
  );

  const applyVersion = useCallback(
    (version: VersionResponse) => {
      dispatch({ type: "REFRESH_VERSION", version });
    },
    [dispatch],
  );

  const handleAdd = useCallback(() => {
    if (!editable || requirementId === null || versionId === null) {
      return;
    }
    const contenido = newContent.trim();
    if (contenido === "") {
      return;
    }
    setBusy(true);
    addCollectionItem(
      requirementId,
      versionId,
      resource,
      kind === undefined ? { contenido } : { contenido, tipo: kind },
    )
      .then((version) => {
        applyVersion(version);
        setNewContent("");
      })
      .catch(reportError)
      .finally(() => setBusy(false));
  }, [applyVersion, editable, kind, newContent, reportError, requirementId, resource, versionId]);

  const handleUpdate = useCallback(() => {
    if (!editable || requirementId === null || versionId === null || editingId === null) {
      return;
    }
    const contenido = editingContent.trim();
    if (contenido === "") {
      return;
    }
    setBusy(true);
    updateCollectionItem(requirementId, versionId, resource, editingId, { contenido })
      .then((version) => {
        applyVersion(version);
        setEditingId(null);
        setEditingContent("");
      })
      .catch(reportError)
      .finally(() => setBusy(false));
  }, [
    applyVersion,
    editable,
    editingContent,
    editingId,
    reportError,
    requirementId,
    resource,
    versionId,
  ]);

  const handleDelete = useCallback(
    (itemId: number) => {
      if (!editable || requirementId === null || versionId === null) {
        return;
      }
      setBusy(true);
      deleteCollectionItem(requirementId, versionId, resource, itemId)
        .then(() => getVersion(requirementId, versionId))
        .then((version) => applyVersion(version))
        .catch(reportError)
        .finally(() => setBusy(false));
    },
    [applyVersion, editable, reportError, requirementId, resource, versionId],
  );

  const handleMove = useCallback(
    (itemId: number, delta: number) => {
      if (!editable || requirementId === null || versionId === null) {
        return;
      }
      const allIds = activeItems.map((item) => item.id as number);
      const subsetIds = visible.map((item) => item.id as number);
      const from = subsetIds.indexOf(itemId);
      const to = from + delta;
      if (from < 0 || to < 0 || to >= subsetIds.length) {
        return;
      }
      const nextSubset = [...subsetIds];
      [nextSubset[from], nextSubset[to]] = [nextSubset[to], nextSubset[from]];
      let cursor = 0;
      const nextAll = allIds.map((id) =>
        subsetIds.includes(id) ? nextSubset[cursor++] : id,
      );
      setBusy(true);
      reorderCollectionItems(requirementId, versionId, resource, nextAll)
        .then((version) => applyVersion(version))
        .catch(reportError)
        .finally(() => setBusy(false));
    },
    [activeItems, applyVersion, editable, reportError, requirementId, resource, versionId, visible],
  );

  const startEdit = useCallback((item: CollectionItemResponse) => {
    setEditingId(item.id);
    setEditingContent(item.contenido);
  }, []);

  const cancelEdit = useCallback(() => {
    setEditingId(null);
    setEditingContent("");
  }, []);

  const disabled = busy || !editable;

  return (
    <div className="space-y-3">
      {!editable && (
        <p className="rounded border border-warning/40 bg-warning/10 px-4 py-2 text-sm text-warning">
          El requerimiento no esta en estado BORRADOR; la edicion esta deshabilitada.
        </p>
      )}

      <ul className="rounded border border-border bg-surface">
        {visible.length === 0 && (
          <li className="px-3 py-4 text-sm text-neutral-dark">
            No hay elementos. Agregue el primero.
          </li>
        )}
        {visible.map((item, index) => (
          <CollectionItemRow
            key={item.id ?? index}
            item={item}
            editing={editingId === item.id}
            editingContent={editingContent}
            disabled={disabled}
            isFirst={index === 0}
            isLast={index === visible.length - 1}
            onStartEdit={() => startEdit(item)}
            onChangeEdit={setEditingContent}
            onSave={handleUpdate}
            onCancel={cancelEdit}
            onDelete={() => {
              if (item.id !== null) {
                handleDelete(item.id);
              }
            }}
            onMoveUp={() => {
              if (item.id !== null) {
                handleMove(item.id, -1);
              }
            }}
            onMoveDown={() => {
              if (item.id !== null) {
                handleMove(item.id, 1);
              }
            }}
          />
        ))}
      </ul>

      {editable && (
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Input
              label={addLabel ?? "Nuevo elemento"}
              value={newContent}
              disabled={disabled}
              onChange={(event) => setNewContent(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  handleAdd();
                }
              }}
            />
          </div>
          <Button disabled={disabled || newContent.trim() === ""} onClick={handleAdd}>
            Agregar
          </Button>
        </div>
      )}
    </div>
  );
}
