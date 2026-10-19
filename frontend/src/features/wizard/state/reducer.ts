/*
 * Reducer del estado del wizard (SPEC-004). Mantiene la captura en cliente y
 * recalcula el estado de cada paso tras cada accion. Sin logica de negocio.
 */

import type { RequirementResponse, VersionResponse } from "../../../api";
import { computeStepStatuses } from "../wizardSteps";
import type {
  WizardAction,
  WizardCollections,
  WizardHeaderFields,
  WizardNarrativeFields,
  WizardSigner,
  WizardSigners,
  WizardState,
} from "./types";

function emptyCollections(): WizardCollections {
  return {
    objetivos: [],
    consideraciones: [],
    beneficios: [],
    restricciones: [],
    volumetria: [],
    riesgos: [],
    "requisitos-futuros": [],
  };
}

function emptyHeader(): WizardHeaderFields {
  return {
    folio: "",
    titulo: "",
    tipo_cambio_id: null,
    sistema: "",
    version_documento: "",
    fecha_version: "",
  };
}

function emptyNarrative(): WizardNarrativeFields {
  return {
    necesidad_actual: "",
    contexto_descripcion: "",
    contexto_manejo_errores: "",
    usuarios_permisos: "",
    requisitos_futuros_aplica: true,
    requisitos_futuros_texto: "",
  };
}

function emptySigner(): WizardSigner {
  return { nombre: "", cargo: "", cargo_id: null };
}

function emptySigners(): WizardSigners {
  return {
    ELABORO: emptySigner(),
    REVISO: emptySigner(),
    AUTORIZO: emptySigner(),
  };
}

export function createInitialWizardState(): WizardState {
  const base: WizardState = {
    requirementId: null,
    folio: null,
    ticket: "",
    estado: null,
    versionId: null,
    header: emptyHeader(),
    narrative: emptyNarrative(),
    signers: emptySigners(),
    collections: emptyCollections(),
    stepIndex: 0,
    stepStatus: [],
    dirty: false,
    saving: false,
    error: null,
  };
  return { ...base, stepStatus: computeStepStatuses(base) };
}

function pickWorkingVersion(requirement: RequirementResponse): VersionResponse | null {
  if (requirement.versiones.length === 0) {
    return null;
  }
  const current = requirement.versiones.find((version) => version.id === requirement.version_actual_id);
  return current ?? requirement.versiones[requirement.versiones.length - 1] ?? null;
}

function signersFromVersion(version: VersionResponse | null): WizardSigners {
  const signers = emptySigners();
  if (version === null) {
    return signers;
  }
  for (const firma of version.firmas) {
    signers[firma.rol] = { nombre: firma.nombre, cargo: firma.cargo, cargo_id: firma.cargo_id };
  }
  return signers;
}

function headerFromVersion(version: VersionResponse | null, folio: number | null): WizardHeaderFields {
  return {
    folio: folio === null ? "" : String(folio),
    titulo: version?.titulo ?? "",
    tipo_cambio_id: version?.tipo_cambio_id ?? null,
    sistema: version?.sistema ?? "",
    version_documento: version?.version_documento ?? "",
    fecha_version: version?.fecha_version ?? "",
  };
}

function narrativeFromVersion(version: VersionResponse | null): WizardNarrativeFields {
  return {
    necesidad_actual: version?.necesidad_actual ?? "",
    contexto_descripcion: version?.contexto_descripcion ?? "",
    contexto_manejo_errores: version?.contexto_manejo_errores ?? "",
    usuarios_permisos: version?.usuarios_permisos ?? "",
    requisitos_futuros_aplica: version?.requisitos_futuros_aplica ?? true,
    requisitos_futuros_texto: version?.requisitos_futuros_texto ?? "",
  };
}

function collectionsFromVersion(version: VersionResponse | null): WizardCollections {
  if (version === null) {
    return emptyCollections();
  }
  return {
    objetivos: version.objetivos,
    consideraciones: version.consideraciones,
    beneficios: version.beneficios,
    restricciones: version.restricciones,
    volumetria: version.volumetria,
    riesgos: version.riesgos,
    "requisitos-futuros": version.requisitos_futuros,
  };
}

function stateFromRequirement(requirement: RequirementResponse): WizardState {
  const version = pickWorkingVersion(requirement);
  const base: WizardState = {
    requirementId: requirement.id,
    folio: requirement.folio,
    ticket: requirement.ticket,
    estado: requirement.estado,
    versionId: version?.id ?? null,
    header: headerFromVersion(version, requirement.folio),
    narrative: narrativeFromVersion(version),
    signers: signersFromVersion(version),
    collections: collectionsFromVersion(version),
    stepIndex: 0,
    stepStatus: [],
    dirty: false,
    saving: false,
    error: null,
  };
  return { ...base, stepStatus: computeStepStatuses(base) };
}

function withStatuses(state: WizardState): WizardState {
  return { ...state, stepStatus: computeStepStatuses(state) };
}

export function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "RESET":
      return createInitialWizardState();
    case "LOAD_REQUIREMENT":
      return stateFromRequirement(action.requirement);
    case "REFRESH_VERSION": {
      const base: WizardState = {
        ...state,
        versionId: action.version.id,
        header: headerFromVersion(action.version, state.folio),
        narrative: narrativeFromVersion(action.version),
        signers: signersFromVersion(action.version),
        collections: collectionsFromVersion(action.version),
        dirty: false,
        saving: false,
        error: null,
      };
      return { ...base, stepStatus: computeStepStatuses(base) };
    }
    case "SET_STEP":
      return withStatuses({ ...state, stepIndex: action.stepIndex, error: null });
    case "SET_HEADER_FIELD": {
      const header = { ...state.header, [action.field]: action.value } as WizardHeaderFields;
      return withStatuses({ ...state, header });
    }
    case "SET_NARRATIVE_FIELD": {
      const narrative = {
        ...state.narrative,
        [action.field]: action.value,
      } as WizardNarrativeFields;
      return withStatuses({ ...state, narrative });
    }
    case "SET_SIGNER_FIELD": {
      const signer = {
        ...state.signers[action.role],
        [action.field]: action.value,
      } as WizardSigner;
      const signers = { ...state.signers, [action.role]: signer };
      return withStatuses({ ...state, signers });
    }
    case "SET_COLLECTION": {
      const collections = {
        ...state.collections,
        [action.resource]: action.items,
      } as WizardCollections;
      return withStatuses({ ...state, collections });
    }
    case "MARK_DIRTY":
      return { ...state, dirty: action.dirty };
    case "SET_SAVING":
      return { ...state, saving: action.saving };
    case "SET_STATUS":
      return withStatuses({ ...state, estado: action.status });
    case "SET_ERROR":
      return withStatuses({ ...state, error: action.error });
  }
}
