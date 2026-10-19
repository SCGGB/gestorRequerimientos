/*
 * DTOs espejo de los esquemas de la API `/api/v1` (backend/app/api/schemas).
 * Contrato de referencia: doc/technical/api.md y /openapi.json.
 * Los nombres de campo se mantienen identicos a la API (snake_case).
 */

export type RequirementStatus =
  | "BORRADOR"
  | "EN_REVISION"
  | "VALIDADO"
  | "APROBADO"
  | "GENERADO"
  | "CANCELADO";

export type BenefitKind = "CUALITATIVO" | "CUANTITATIVO";

export type SignatureRole = "ELABORO" | "REVISO" | "AUTORIZO";

export interface CollectionItemResponse {
  id: number | null;
  contenido: string;
  orden: number;
  activo: boolean;
}

export interface BenefitResponse extends CollectionItemResponse {
  tipo: BenefitKind;
}

export interface SignatureResponse {
  id: number | null;
  rol: SignatureRole;
  nombre: string;
  cargo: string;
  cargo_id: number | null;
}

export interface AttachmentResponse {
  id: number | null;
  nombre: string;
  tipo_mime: string | null;
  orden: number;
  leyenda: string | null;
  storage_key: string;
  activo: boolean;
}

export interface VersionResponse {
  id: number | null;
  numero: number;
  titulo: string;
  tipo_cambio_id: number | null;
  sistema: string | null;
  version_documento: string;
  fecha_version: string;
  necesidad_actual: string | null;
  contexto_descripcion: string | null;
  contexto_manejo_errores: string | null;
  usuarios_permisos: string | null;
  requisitos_futuros_aplica: boolean;
  requisitos_futuros_texto: string | null;
  campos_dinamicos: Record<string, unknown>;
  congelada: boolean;
  objetivos: CollectionItemResponse[];
  consideraciones: CollectionItemResponse[];
  beneficios: BenefitResponse[];
  restricciones: CollectionItemResponse[];
  volumetria: CollectionItemResponse[];
  riesgos: CollectionItemResponse[];
  requisitos_futuros: CollectionItemResponse[];
  firmas: SignatureResponse[];
  anexos: AttachmentResponse[];
}

export interface RequirementResponse {
  id: number;
  folio: number;
  ticket: string;
  estado: RequirementStatus;
  version_actual_id: number | null;
  versiones: VersionResponse[];
}

export interface RequirementSummary {
  id: number;
  folio: number;
  ticket: string;
  titulo: string;
  estado: RequirementStatus;
  version_actual_id: number | null;
}

export interface RequirementPage {
  items: RequirementSummary[];
  total: number;
  page: number;
  size: number;
}

export type PreviewBlockType = "parrafo" | "lista" | "no_aplica";

export interface PreviewBlock {
  tipo: PreviewBlockType;
  texto: string | null;
  items: string[] | null;
}

export interface PreviewSection {
  codigo: string;
  numero: string;
  titulo: string;
  bloques: PreviewBlock[];
}

export interface PreviewVersionRow {
  version: string;
  fecha: string;
  descripcion_cambio: string | null;
  reviso: string | null;
  elaboro: string | null;
}

export interface PreviewSigner {
  nombre: string;
  cargo: string | null;
}

export interface PreviewFirmas {
  elaboro: PreviewSigner | null;
  reviso: PreviewSigner | null;
  autorizo: PreviewSigner | null;
}

export interface PreviewDocument {
  folio: number;
  ticket: string;
  titulo: string;
  version_documento: string;
  fecha_version: string;
  secciones: PreviewSection[];
  control_versiones: PreviewVersionRow[];
  firmas: PreviewFirmas;
}

export interface ChangeTypeResponse {
  id: number | null;
  codigo: string;
  nombre: string;
  activo: boolean;
}

export interface PositionResponse {
  id: number | null;
  rol: SignatureRole;
  nombre: string;
  predeterminado: boolean;
  activo: boolean;
}

/* ---- Payloads de entrada ---- */

export interface RequirementCreatePayload {
  folio: number;
  titulo: string;
  tipo_cambio_id: number;
  sistema: string;
  version_documento: string;
  fecha_version: string;
}

export interface VersionUpdatePayload {
  titulo?: string;
  tipo_cambio_id?: number;
  sistema?: string;
  version_documento?: string;
  fecha_version?: string;
  necesidad_actual?: string;
  contexto_descripcion?: string;
  contexto_manejo_errores?: string;
  usuarios_permisos?: string;
  requisitos_futuros_aplica?: boolean;
  requisitos_futuros_texto?: string;
  campos_dinamicos?: Record<string, unknown>;
}

export interface CollectionItemCreatePayload {
  contenido: string;
  orden?: number;
}

export interface BenefitCreatePayload extends CollectionItemCreatePayload {
  tipo: BenefitKind;
}

export interface CollectionItemUpdatePayload {
  contenido: string;
}

export interface ReorderPayload {
  ids: number[];
}

export interface RequirementListParams {
  estado?: RequirementStatus | "";
  folio?: number;
  page?: number;
  size?: number;
}

/* ---- Enums y etiquetas de UI ---- */

export const COLLECTION_RESOURCES = [
  "objetivos",
  "consideraciones",
  "beneficios",
  "restricciones",
  "volumetria",
  "riesgos",
  "requisitos-futuros",
] as const;

export type CollectionResource = (typeof COLLECTION_RESOURCES)[number];

export const REQUIREMENT_STATUS_LABELS: Record<RequirementStatus, string> = {
  BORRADOR: "Borrador",
  EN_REVISION: "En Revision",
  VALIDADO: "Validado",
  APROBADO: "Aprobado",
  GENERADO: "Generado",
  CANCELADO: "Cancelado",
};

export type StatusTone = "success" | "warning" | "danger" | "neutral" | "info";

export const REQUIREMENT_STATUS_TONES: Record<RequirementStatus, StatusTone> = {
  BORRADOR: "neutral",
  EN_REVISION: "warning",
  VALIDADO: "success",
  APROBADO: "success",
  GENERADO: "info",
  CANCELADO: "danger",
};

export const SIGNATURE_ROLE_LABELS: Record<SignatureRole, string> = {
  ELABORO: "Elaboro",
  REVISO: "Reviso",
  AUTORIZO: "Autorizo",
};

export const BENEFIT_KIND_LABELS: Record<BenefitKind, string> = {
  CUALITATIVO: "Cualitativos",
  CUANTITATIVO: "Cuantitativos",
};
