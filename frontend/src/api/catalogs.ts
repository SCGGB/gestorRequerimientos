import { request } from "./client";
import type { ChangeTypeResponse, PositionResponse, SignatureRole } from "./types";

export function listChangeTypes(): Promise<ChangeTypeResponse[]> {
  return request<ChangeTypeResponse[]>("/catalogos/tipos-cambio");
}

export function listPositions(rol?: SignatureRole): Promise<PositionResponse[]> {
  const query = rol === undefined ? "" : `?rol=${rol}`;
  return request<PositionResponse[]>(`/catalogos/cargos${query}`);
}
