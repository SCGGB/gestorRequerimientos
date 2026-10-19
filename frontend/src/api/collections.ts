import { request } from "./client";
import type {
  BenefitCreatePayload,
  CollectionItemCreatePayload,
  CollectionItemUpdatePayload,
  CollectionResource,
  VersionResponse,
} from "./types";

function basePath(
  requirementId: number,
  versionId: number,
  resource: CollectionResource,
): string {
  return `/requerimientos/${requirementId}/versiones/${versionId}/${resource}`;
}

export function addCollectionItem(
  requirementId: number,
  versionId: number,
  resource: CollectionResource,
  payload: CollectionItemCreatePayload | BenefitCreatePayload,
): Promise<VersionResponse> {
  return request<VersionResponse>(basePath(requirementId, versionId, resource), {
    method: "POST",
    body: payload,
  });
}

export function updateCollectionItem(
  requirementId: number,
  versionId: number,
  resource: CollectionResource,
  itemId: number,
  payload: CollectionItemUpdatePayload,
): Promise<VersionResponse> {
  return request<VersionResponse>(
    `${basePath(requirementId, versionId, resource)}/${itemId}`,
    { method: "PATCH", body: payload },
  );
}

export function deleteCollectionItem(
  requirementId: number,
  versionId: number,
  resource: CollectionResource,
  itemId: number,
): Promise<void> {
  return request<void>(`${basePath(requirementId, versionId, resource)}/${itemId}`, {
    method: "DELETE",
  });
}

export function reorderCollectionItems(
  requirementId: number,
  versionId: number,
  resource: CollectionResource,
  ids: number[],
): Promise<VersionResponse> {
  return request<VersionResponse>(
    `${basePath(requirementId, versionId, resource)}/orden`,
    { method: "PUT", body: { ids } },
  );
}
