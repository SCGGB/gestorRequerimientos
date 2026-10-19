import { useContext } from "react";

import { WizardContext } from "./WizardProvider";
import type { WizardContextValue } from "./WizardProvider";

export function useWizard(): WizardContextValue {
  const context = useContext(WizardContext);
  if (context === null) {
    throw new Error("useWizard debe usarse dentro de WizardProvider");
  }
  return context;
}
