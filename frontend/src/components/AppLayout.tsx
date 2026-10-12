import type { ReactNode } from "react";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas font-sans text-secondary">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center gap-3 px-margin-mobile sm:px-margin">
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
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-margin-mobile py-8 sm:px-margin">
        {children}
      </main>

      <footer className="border-t border-border bg-surface">
        <div className="mx-auto w-full max-w-7xl px-margin-mobile py-4 text-xs text-neutral-dark sm:px-margin">
          Sistema de Especificacion de Requerimientos de Software
        </div>
      </footer>
    </div>
  );
}
