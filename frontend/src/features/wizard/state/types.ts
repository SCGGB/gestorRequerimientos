/*
 * Modelo de estado del wizard de captura (SPEC-004).
 * Sin logica de negocio: solo captura, validacion de forma por paso y presentacion.
 * La fuente de verdad sigue siendo la API `/api/v1` (SPEC-003).
 */

import type {
  BenefitResponse,
  CollectionItemResponse,
  CollectionResource,
  RequirementResponse,
  RequirementStatus,
  SignatureRole,
  VersionResponse,
} from "../../../api";

export type WizardStepStatus = "pendiente" | "activo" | "completado" | "error";

export interface WizardHeaderFields {
  folio: string;
  titulo: string;
  tipo_cambio_id: number | null;
  sistema: string;
  version_documento: string;
  fecha_version: string;
}

export interface WizardNarrativeFields {
  necesidad_actual: string;
  contexto_descripcion: string;
  contexto_manejo_errores: string;
  usuarios_permisos: string;
  requisitos_futuros_aplica: boolean;
  requisitos_futuros_texto: string;
}

export interface WizardSigner {
  nombre: string;
  cargo: string;
  cargo_id: number | null;
}

export type WizardSigners = Record<SignatureRole, WizardSigner>;

export interface WizardCollections {
  objetivos: CollectionItemResponse[];
  consideraciones: CollectionItemResponse[];
  beneficios: BenefitResponse[];
  restricciones: CollectionItemResponse[];
  volumetria: CollectionItemResponse[];
  riesgos: CollectionItemResponse[];
  "requisitos-futuros": CollectionItemResponse[];
}

export interface WizardError {
  code: string;
  message: string;
  details: unknown;
  stepIndex?: number;
}

export interface WizardState {
  requirementId: number | null;
  folio: number | null;
  ticket: string;
  estado: RequirementStatus | null;
  versionId: number | null;
  header: WizardHeaderFields;
  narrative: WizardNarrativeFields;
  signers: WizardSigners;
  collections: WizardCollections;
  stepIndex: number;
  stepStatus: WizardStepStatus[];
  dirty: boolean;
  saving: boolean;
  error: WizardError | null;
}

export type WizardAction =
  | { type: "RESET" }
  | { type: "LOAD_REQUIREMENT"; requirement: RequirementResponse }
  | { type: "REFRESH_VERSION"; version: VersionResponse }
  | { type: "SET_STEP"; stepIndex: number }
  | {
      type: "SET_HEADER_FIELD";
      field: keyof WizardHeaderFields;
      value: string | number | null;
    }
  | {
      type: "SET_NARRATIVE_FIELD";
      field: keyof WizardNarrativeFields;
      value: string | boolean;
    }
  | {
      type: "SET_SIGNER_FIELD";
      role: SignatureRole;
      field: keyof WizardSigner;
      value: string | number | null;
    }
  | {
      type: "SET_COLLECTION";
      resource: CollectionResource;
      items: CollectionItemResponse[] | BenefitResponse[];
    }
  | { type: "MARK_DIRTY"; dirty: boolean }
  | { type: "SET_SAVING"; saving: boolean }
  | { type: "SET_STATUS"; status: RequirementStatus }
  | { type: "SET_ERROR"; error: WizardError | null };
