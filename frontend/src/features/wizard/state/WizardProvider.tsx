import { createContext, useMemo, useReducer } from "react";
import type { Dispatch, ReactNode } from "react";

import { createInitialWizardState, wizardReducer } from "./reducer";
import type { WizardAction, WizardState } from "./types";

export interface WizardContextValue {
  state: WizardState;
  dispatch: Dispatch<WizardAction>;
}

export const WizardContext = createContext<WizardContextValue | null>(null);

export function WizardProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(wizardReducer, undefined, createInitialWizardState);

  const value = useMemo<WizardContextValue>(
    () => ({ state, dispatch }),
    [state],
  );

  return <WizardContext.Provider value={value}>{children}</WizardContext.Provider>;
}
