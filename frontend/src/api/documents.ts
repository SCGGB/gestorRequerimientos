import { request, requestBlob } from "./client";
import type { BlobResponse } from "./client";
import type { GeneratedDocument } from "./types";

export function generateDocuments(
  requirementId: number,
): Promise<GeneratedDocument[]> {
  return request<GeneratedDocument[]>(
    `/requerimientos/${requirementId}/documentos`,
    { method: "POST" },
  );
}

export function listDocuments(
  requirementId: number,
  signal?: AbortSignal,
): Promise<GeneratedDocument[]> {
  return request<GeneratedDocument[]>(
    `/requerimientos/${requirementId}/documentos`,
    { signal },
  );
}

export function downloadDocument(
  requirementId: number,
  documentId: number,
): Promise<BlobResponse> {
  return requestBlob(
    `/requerimientos/${requirementId}/documentos/${documentId}/descarga`,
  );
}
