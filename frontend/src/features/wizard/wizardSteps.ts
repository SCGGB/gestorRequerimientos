/*
 * Definicion de los 13 pasos del wizard (SPEC-004, RF-04/RF-05/CA-05).
 * Cada paso declara sus obligatorios y la funcion `isComplete` usada por el
 * stepper y por el bloqueo de "siguiente". Solo valida forma y obligatorios
 * en el cliente; la validacion integral corresponde a SPEC-005.
 */

import type { CollectionItemResponse, CollectionResource } from "../../api";
import type { WizardState, WizardStepStatus } from "./state/types";

export type WizardStepId =
  | "generalData"
  | "currentNeed"
  | "objectives"
  | "considerations"
  | "benefits"
  | "context"
  | "usersPermissions"
  | "restrictions"
  | "futureRequirements"
  | "volumetry"
  | "risks"
  | "documentControl"
  | "review";

export interface WizardStepDefinition {
  id: WizardStepId;
  numero: number;
  titulo: string;
  componente: string;
  recurso?: CollectionResource;
  obligatorios: string[];
}

export const WIZARD_STEPS: readonly WizardStepDefinition[] = [
  {
    id: "generalData",
    numero: 1,
    titulo: "Datos generales",
    componente: "Step01GeneralData",
    obligatorios: ["folio", "titulo", "tipo de cambio", "sistema", "version documental", "fecha de version"],
  },
  {
    id: "currentNeed",
    numero: 2,
    titulo: "Necesidad actual",
    componente: "Step02CurrentNeed",
    obligatorios: ["necesidad actual"],
  },
  {
    id: "objectives",
    numero: 3,
    titulo: "Objetivos generales",
    componente: "Step03Objectives",
    recurso: "objetivos",
    obligatorios: ["al menos 1 objetivo"],
  },
  {
    id: "considerations",
    numero: 4,
    titulo: "Consideraciones",
    componente: "Step04Considerations",
    recurso: "consideraciones",
    obligatorios: ["al menos 1 consideracion"],
  },
  {
    id: "benefits",
    numero: 5,
    titulo: "Beneficios esperados",
    componente: "Step05Benefits",
    recurso: "beneficios",
    obligatorios: ["al menos 1 beneficio"],
  },
  {
    id: "context",
    numero: 6,
    titulo: "Diagramas contextuales",
    componente: "Step06Context",
    obligatorios: ["descripcion contextual"],
  },
  {
    id: "usersPermissions",
    numero: 7,
    titulo: "Usuarios y permisos",
    componente: "Step07UsersPermissions",
    obligatorios: ["usuarios y permisos"],
  },
  {
    id: "restrictions",
    numero: 8,
    titulo: "Restricciones",
    componente: "Step08Restrictions",
    recurso: "restricciones",
    obligatorios: ["al menos 1 restriccion"],
  },
  {
    id: "futureRequirements",
    numero: 9,
    titulo: "Requisitos futuros",
    componente: "Step09FutureRequirements",
    recurso: "requisitos-futuros",
    obligatorios: ["texto o al menos 1 requisito futuro cuando aplica"],
  },
  {
    id: "volumetry",
    numero: 10,
    titulo: "Volumetria y rendimiento",
    componente: "Step10Volumetry",
    recurso: "volumetria",
    obligatorios: ["al menos 1 elemento de volumetria"],
  },
  {
    id: "risks",
    numero: 11,
    titulo: "Riesgos iniciales",
    componente: "Step11Risks",
    recurso: "riesgos",
    obligatorios: ["al menos 1 riesgo"],
  },
  {
    id: "documentControl",
    numero: 12,
    titulo: "Control documental",
    componente: "Step12DocumentControl",
    obligatorios: ["nombre de Elaboro", "nombre de Autorizo"],
  },
  {
    id: "review",
    numero: 13,
    titulo: "Revision",
    componente: "Step13Review",
    obligatorios: [],
  },
];

function isBlank(value: string | null | undefined): boolean {
  return value === null || value === undefined || value.trim() === "";
}

function isPositiveInteger(value: string): boolean {
  return /^\d+$/.test(value.trim()) && Number(value) >= 1;
}

function countActive(items: readonly CollectionItemResponse[]): number {
  return items.filter((item) => item.activo !== false).length;
}

export function isComplete(state: WizardState, step: WizardStepDefinition): boolean {
  switch (step.id) {
    case "generalData": {
      const { folio, titulo, tipo_cambio_id, sistema, version_documento, fecha_version } = state.header;
      return (
        isPositiveInteger(folio) &&
        !isBlank(titulo) &&
        tipo_cambio_id !== null &&
        !isBlank(sistema) &&
        !isBlank(version_documento) &&
        !isBlank(fecha_version)
      );
    }
    case "currentNeed":
      return !isBlank(state.narrative.necesidad_actual);
    case "objectives":
      return countActive(state.collections.objetivos) >= 1;
    case "considerations":
      return countActive(state.collections.consideraciones) >= 1;
    case "benefits":
      return countActive(state.collections.beneficios) >= 1;
    case "context":
      return !isBlank(state.narrative.contexto_descripcion);
    case "usersPermissions":
      return !isBlank(state.narrative.usuarios_permisos);
    case "restrictions":
      return countActive(state.collections.restricciones) >= 1;
    case "futureRequirements":
      return (
        !state.narrative.requisitos_futuros_aplica ||
        !isBlank(state.narrative.requisitos_futuros_texto) ||
        countActive(state.collections["requisitos-futuros"]) >= 1
      );
    case "volumetry":
      return countActive(state.collections.volumetria) >= 1;
    case "risks":
      return countActive(state.collections.riesgos) >= 1;
    case "documentControl":
      return (
        !isBlank(state.signers.ELABORO.nombre) &&
        !isBlank(state.signers.AUTORIZO.nombre)
      );
    case "review":
      return true;
  }
}

export function completionIssue(state: WizardState, step: WizardStepDefinition): string | null {
  if (isComplete(state, step)) {
    return null;
  }
  const missing = step.obligatorios.join(", ");
  return `Complete los obligatorios del paso ${step.numero}: ${missing}.`;
}

export function computeStepStatuses(state: WizardState): WizardStepStatus[] {
  return WIZARD_STEPS.map((step, index) => {
    if (index === state.stepIndex) {
      return state.error?.stepIndex === index ? "error" : "activo";
    }
    return isComplete(state, step) ? "completado" : "pendiente";
  });
}
