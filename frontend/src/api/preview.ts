import { request } from "./client";
import type { PreviewDocument } from "./types";

export function getPreview(
  requirementId: number,
  versionId: number,
  signal?: AbortSignal,
): Promise<PreviewDocument> {
  return request<PreviewDocument>(
    `/requerimientos/${requirementId}/versiones/${versionId}/vista-previa`,
    { signal },
  );
}
