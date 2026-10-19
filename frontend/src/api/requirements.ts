import { request } from "./client";
import type {
  RequirementCreatePayload,
  RequirementListParams,
  RequirementPage,
  RequirementResponse,
  VersionResponse,
  VersionUpdatePayload,
} from "./types";

function buildQuery(params: RequirementListParams): string {
  const search = new URLSearchParams();
  if (params.estado !== undefined && params.estado !== "") {
    search.set("estado", params.estado);
  }
  if (params.folio !== undefined) {
    search.set("folio", String(params.folio));
  }
  if (params.page !== undefined) {
    search.set("page", String(params.page));
  }
  if (params.size !== undefined) {
    search.set("size", String(params.size));
  }
  const query = search.toString();
  return query === "" ? "" : `?${query}`;
}

export function listRequirements(
  params: RequirementListParams = {},
): Promise<RequirementPage> {
  return request<RequirementPage>(`/requerimientos${buildQuery(params)}`);
}

export function createRequirement(
  payload: RequirementCreatePayload,
): Promise<RequirementResponse> {
  return request<RequirementResponse>("/requerimientos", {
    method: "POST",
    body: payload,
  });
}

export function getRequirement(id: number): Promise<RequirementResponse> {
  return request<RequirementResponse>(`/requerimientos/${id}`);
}

export function listVersions(id: number): Promise<VersionResponse[]> {
  return request<VersionResponse[]>(`/requerimientos/${id}/versiones`);
}

export function getVersion(
  id: number,
  versionId: number,
): Promise<VersionResponse> {
  return request<VersionResponse>(
    `/requerimientos/${id}/versiones/${versionId}`,
  );
}

export function updateVersion(
  id: number,
  versionId: number,
  payload: VersionUpdatePayload,
): Promise<VersionResponse> {
  return request<VersionResponse>(
    `/requerimientos/${id}/versiones/${versionId}`,
    { method: "PATCH", body: payload },
  );
}
