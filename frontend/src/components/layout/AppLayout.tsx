import type { ReactNode } from "react";

import { useNav } from "../../navigation/NavContext";
import { Button } from "../ui/Button";
import { Sidebar } from "./Sidebar";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { activeKey, navigate } = useNav();

  return (
    <div className="flex min-h-screen flex-col bg-canvas font-sans text-secondary">
      <header className="border-b border-border bg-surface">
        <div className="flex h-16 w-full items-center gap-3 px-margin-mobile sm:px-margin">
          <div
            data-testid="brand-badge"
            className="flex h-9 w-9 items-center justify-center rounded bg-primary text-sm font-bold text-on-primary"
          >
            SC
          </div>
          <div className="leading-tight">
            <p className="text-base font-semibold text-secondary">
              Gestor de Requerimientos
            </p>
            <p className="text-xs text-neutral-dark">
              Especificacion de Requerimientos de Software
            </p>
          </div>
          <div className="ml-auto">
            <Button
              variant="secondary"
              size="sm"
              aria-current={activeKey === "overview" ? "page" : undefined}
              onClick={() => navigate({ name: "overview" }, "overview")}
            >
              Estado del sistema
            </Button>
          </div>
        </div>
      </header>

      <div className="flex w-full flex-1 flex-col md:flex-row">
        <Sidebar />
        <main className="flex-1 px-margin-mobile py-8 sm:px-margin">
          {children}
        </main>
      </div>

      <footer className="border-t border-border bg-surface">
        <div className="px-margin-mobile py-4 text-xs text-neutral-dark sm:px-margin">
          Sistema de Especificacion de Requerimientos de Software
        </div>
      </footer>
    </div>
  );
}
