import { useCallback, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { AuthProvider, useAuth } from "./auth/AuthContext";
import { LoginOverlay } from "./auth/LoginOverlay";
import { AppLayout } from "./components/layout/AppLayout";
import { PlaceholderPage } from "./components/layout/PlaceholderPage";
import { RequirementsListPage } from "./features/requirements/RequirementsListPage";
import { UsersPage } from "./features/users/UsersPage";
import { WizardPage } from "./features/wizard/WizardPage";
import { WizardProvider } from "./features/wizard/state/WizardProvider";
import { NavContext } from "./navigation/NavContext";
import type { AppView, SidebarKey } from "./navigation/NavContext";
import { OverviewPage } from "./pages/OverviewPage";

function renderView(view: AppView): ReactNode {
  switch (view.name) {
    case "list":
      return <RequirementsListPage />;
    case "wizard":
      return (
        <WizardProvider>
          <WizardPage />
        </WizardProvider>
      );
    case "placeholder":
      return <PlaceholderPage title={view.title} />;
    case "overview":
      return <OverviewPage />;
    case "users":
      return <UsersPage />;
  }
}

function AppContent() {
  const { status } = useAuth();
  const [view, setView] = useState<AppView>({ name: "list" });
  const [activeKey, setActiveKey] = useState<SidebarKey>("requirements");

  const navigate = useCallback((next: AppView, key: SidebarKey) => {
    setView(next);
    setActiveKey(key);
  }, []);

  const value = useMemo(
    () => ({ view, activeKey, navigate }),
    [view, activeKey, navigate],
  );

  return (
    <NavContext.Provider value={value}>
      <AppLayout>{renderView(view)}</AppLayout>
      {status !== "authenticated" && <LoginOverlay />}
    </NavContext.Provider>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
