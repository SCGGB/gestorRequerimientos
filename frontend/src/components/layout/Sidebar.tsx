import { useNav } from "../../navigation/NavContext";
import type { AppView, SidebarKey } from "../../navigation/NavContext";

interface NavItem {
  key: SidebarKey;
  label: string;
  view: AppView;
}

const items: NavItem[] = [
  { key: "requirements", label: "Requerimientos", view: { name: "list" } },
  {
    key: "new-requirement",
    label: "Nuevo Requerimiento",
    view: { name: "wizard" },
  },
  {
    key: "templates",
    label: "Plantillas ERS/SRS",
    view: { name: "placeholder", title: "Plantillas ERS/SRS" },
  },
  {
    key: "repository",
    label: "Repositorio Documental",
    view: { name: "placeholder", title: "Repositorio Documental" },
  },
  {
    key: "settings",
    label: "Configuracion y Catalogos",
    view: { name: "placeholder", title: "Configuracion y Catalogos" },
  },
];

export function Sidebar() {
  const { activeKey, navigate } = useNav();

  return (
    <nav
      aria-label="Navegacion principal"
      data-print-hide
      className="w-full shrink-0 border-b border-border bg-surface md:w-64 md:border-b-0 md:border-r"
    >
      <ul className="flex gap-1 overflow-x-auto p-2 md:flex-col md:overflow-visible md:p-4">
        {items.map((item) => {
          const active = item.key === activeKey;
          return (
            <li key={item.key} className="shrink-0 md:w-full">
              <button
                type="button"
                aria-current={active ? "page" : undefined}
                onClick={() => navigate(item.view, item.key)}
                className={`w-full whitespace-nowrap rounded px-3 py-2 text-left text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-primary/25 ${
                  active
                    ? "bg-primary text-on-primary"
                    : "text-neutral-dark hover:bg-muted"
                }`}
              >
                {item.label}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
