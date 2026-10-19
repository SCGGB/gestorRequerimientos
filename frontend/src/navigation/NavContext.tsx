import { createContext, useContext } from "react";

export type AppView =
  | { name: "list" }
  | { name: "wizard"; requirementId?: number }
  | { name: "placeholder"; title: string }
  | { name: "overview" };

export type SidebarKey =
  | "requirements"
  | "new-requirement"
  | "templates"
  | "repository"
  | "settings"
  | "overview";

export interface NavContextValue {
  view: AppView;
  activeKey: SidebarKey;
  navigate: (view: AppView, key: SidebarKey) => void;
}

export const NavContext = createContext<NavContextValue | null>(null);

export function useNav(): NavContextValue {
  const context = useContext(NavContext);
  if (context === null) {
    throw new Error("useNav debe usarse dentro de NavContext.Provider");
  }
  return context;
}
