import { ApiError } from "../../../api";
import type { WizardError } from "./types";

export function toWizardError(err: unknown, stepIndex?: number): WizardError {
  if (err instanceof ApiError) {
    return {
      code: err.code,
      message: err.message,
      details: err.details,
      stepIndex,
    };
  }
  return {
    code: "unexpected_error",
    message: err instanceof Error ? err.message : "Error inesperado.",
    details: null,
    stepIndex,
  };
}
