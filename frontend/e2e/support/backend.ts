/*
 * Backend simulado para pruebas e2e: intercepta `/api/v1/**` con Playwright
 * `page.route` y mantiene un estado minimo en memoria (SPEC-004, T-19).
 */

import type { Page } from "@playwright/test";

const COLLECTION_KEYS = [
  "objetivos",
  "consideraciones",
  "beneficios",
  "restricciones",
  "volumetria",
  "riesgos",
  "requisitos-futuros",
] as const;

type CollectionKey = (typeof COLLECTION_KEYS)[number];

interface Item {
  id: number;
  contenido: string;
  orden: number;
  activo: boolean;
  tipo?: "CUALITATIVO" | "CUANTITATIVO";
}

const HEADER_KEYS = [
  "titulo",
  "tipo_cambio_id",
  "sistema",
  "version_documento",
  "fecha_version",
];

const NARRATIVE_KEYS = [
  "necesidad_actual",
  "contexto_descripcion",
  "contexto_manejo_errores",
  "usuarios_permisos",
  "requisitos_futuros_aplica",
  "requisitos_futuros_texto",
];

export interface BackendState {
  total: number;
  createError: { status: number; code: string; message: string } | null;
  previewError: { status: number; code: string; message: string } | null;
  captured: {
    createBodies: Array<Record<string, unknown>>;
    patchBodies: Array<Record<string, unknown>>;
    collectionPosts: Array<{ resource: string; body: Record<string, unknown> }>;
    listQueries: string[];
  };
  collections: Record<CollectionKey, Item[]>;
}

export interface PreviewDocumentMock {
  folio: number;
  ticket: string;
  titulo: string;
  version_documento: string;
  fecha_version: string;
  secciones: Array<{
    codigo: string;
    numero: string;
    titulo: string;
    bloques: Array<{
      tipo: "parrafo" | "lista" | "no_aplica";
      texto: string | null;
      items: string[] | null;
    }>;
  }>;
  control_versiones: Array<{
    version: string;
    fecha: string;
    descripcion_cambio: string | null;
    reviso: string | null;
    elaboro: string | null;
  }>;
  firmas: {
    elaboro: { nombre: string; cargo: string | null } | null;
    reviso: { nombre: string; cargo: string | null } | null;
    autorizo: { nombre: string; cargo: string | null } | null;
  };
}

export function previewDocument(
  overrides: Partial<PreviewDocumentMock> = {},
): PreviewDocumentMock {
  return {
    folio: 123,
    ticket: "T#123",
    titulo: "Titulo de prueba",
    version_documento: "1.0",
    fecha_version: "16-10-2026",
    secciones: [
      {
        codigo: "objetivo",
        numero: "1",
        titulo: "Objetivo general",
        bloques: [{ tipo: "parrafo", texto: "Objetivo de la vista previa", items: null }],
      },
      {
        codigo: "objetivos",
        numero: "2",
        titulo: "Objetivos especificos",
        bloques: [{ tipo: "lista", texto: null, items: ["Objetivo uno", "Objetivo dos"] }],
      },
      {
        codigo: "beneficios",
        numero: "3",
        titulo: "Beneficios",
        bloques: [{ tipo: "no_aplica", texto: "No aplica", items: null }],
      },
    ],
    control_versiones: [
      {
        version: "1.0",
        fecha: "16-10-2026",
        descripcion_cambio: null,
        reviso: null,
        elaboro: "Ana Elaboro",
      },
    ],
    firmas: {
      elaboro: { nombre: "Ana Elaboro", cargo: "Analista" },
      reviso: null,
      autorizo: null,
    },
    ...overrides,
  };
}

function emptyCollections(): Record<CollectionKey, Item[]> {
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

export function installBackend(page: Page): BackendState {
  const state: BackendState = {
    total: 1,
    createError: null,
    previewError: null,
    captured: {
      createBodies: [],
      patchBodies: [],
      collectionPosts: [],
      listQueries: [],
    },
    collections: emptyCollections(),
  };

  let nextItemId = 100;
  let folio = 0;
  let ticket = "";
  let titulo = "";
  const header: Record<string, unknown> = {};
  const narrative: Record<string, unknown> = { requisitos_futuros_aplica: true };

  function versionResponse() {
    return {
      id: 1,
      numero: 1,
      titulo,
      tipo_cambio_id: header.tipo_cambio_id ?? null,
      sistema: header.sistema ?? null,
      version_documento: header.version_documento ?? "",
      fecha_version: header.fecha_version ?? "",
      necesidad_actual: narrative.necesidad_actual ?? null,
      contexto_descripcion: narrative.contexto_descripcion ?? null,
      contexto_manejo_errores: narrative.contexto_manejo_errores ?? null,
      usuarios_permisos: narrative.usuarios_permisos ?? null,
      requisitos_futuros_aplica: narrative.requisitos_futuros_aplica ?? true,
      requisitos_futuros_texto: narrative.requisitos_futuros_texto ?? null,
      campos_dinamicos: {},
      congelada: false,
      objetivos: state.collections.objetivos,
      consideraciones: state.collections.consideraciones,
      beneficios: state.collections.beneficios,
      restricciones: state.collections.restricciones,
      volumetria: state.collections.volumetria,
      riesgos: state.collections.riesgos,
      requisitos_futuros: state.collections["requisitos-futuros"],
      firmas: [],
      anexos: [],
    };
  }

  function requirementResponse() {
    return {
      id: 1,
      folio,
      ticket,
      estado: "BORRADOR",
      version_actual_id: 1,
      versiones: [versionResponse()],
    };
  }

  void page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const path = url.pathname.replace(/^\/api\/v1/, "");

    if (path === "/catalogos/tipos-cambio" && method === "GET") {
      await route.fulfill({
        json: [{ id: 1, codigo: "MEJ", nombre: "Mejora", activo: true }],
      });
      return;
    }

    if (path === "/catalogos/cargos" && method === "GET") {
      const rol = url.searchParams.get("rol") ?? "ELABORO";
      await route.fulfill({
        json: [{ id: 10, rol, nombre: `Cargo ${rol}`, predeterminado: true, activo: true }],
      });
      return;
    }

    if (path === "/requerimientos" && method === "GET") {
      state.captured.listQueries.push(url.search);
      await route.fulfill({
        json: {
          items: [
            {
              id: 1,
              folio: folio === 0 ? 1 : folio,
              ticket: ticket === "" ? "T#1" : ticket,
              titulo: titulo === "" ? "Titulo de prueba" : titulo,
              estado: "BORRADOR",
              version_actual_id: 1,
            },
          ],
          total: state.total,
          page: Number(url.searchParams.get("page") ?? "1"),
          size: 10,
        },
      });
      return;
    }

    if (path === "/requerimientos" && method === "POST") {
      const body = JSON.parse(request.postData() ?? "{}") as Record<string, unknown>;
      state.captured.createBodies.push(body);
      if (state.createError !== null) {
        await route.fulfill({
          status: state.createError.status,
          json: {
            error: {
              code: state.createError.code,
              message: state.createError.message,
              details: null,
            },
          },
        });
        return;
      }
      folio = Number(body.folio);
      titulo = String(body.titulo);
      ticket = `T#${folio}`;
      for (const key of HEADER_KEYS) {
        if (key in body) {
          header[key] = body[key];
        }
      }
      await route.fulfill({ status: 201, json: requirementResponse() });
      return;
    }

    let match = path.match(/^\/requerimientos\/(\d+)\/versiones\/(\d+)$/);
    if (match !== null && method === "PATCH") {
      const body = JSON.parse(request.postData() ?? "{}") as Record<string, unknown>;
      state.captured.patchBodies.push(body);
      for (const [key, value] of Object.entries(body)) {
        if (HEADER_KEYS.includes(key)) {
          header[key] = value;
        }
        if (NARRATIVE_KEYS.includes(key)) {
          narrative[key] = value;
        }
      }
      if ("titulo" in body) {
        titulo = String(body.titulo);
      }
      await route.fulfill({ json: versionResponse() });
      return;
    }

    if (match !== null && method === "GET") {
      await route.fulfill({ json: versionResponse() });
      return;
    }

    match = path.match(/^\/requerimientos\/(\d+)$/);
    if (match !== null && method === "GET") {
      await route.fulfill({ json: requirementResponse() });
      return;
    }

    match = path.match(/^\/requerimientos\/(\d+)\/versiones\/(\d+)\/vista-previa$/);
    if (match !== null && method === "GET") {
      if (state.previewError !== null) {
        await route.fulfill({
          status: state.previewError.status,
          json: {
            error: {
              code: state.previewError.code,
              message: state.previewError.message,
              details: null,
            },
          },
        });
        return;
      }
      await route.fulfill({ json: previewDocument({ folio: folio === 0 ? 123 : folio }) });
      return;
    }

    match = path.match(/^\/requerimientos\/(\d+)\/versiones\/(\d+)\/([a-z-]+)\/orden$/);
    if (match !== null && method === "PUT") {
      const resource = match[3] as CollectionKey;
      const body = JSON.parse(request.postData() ?? "{}") as { ids: number[] };
      const byId = new Map(state.collections[resource].map((item) => [item.id, item]));
      state.collections[resource] = body.ids.map((id, index) => ({
        ...(byId.get(id) as Item),
        orden: index + 1,
      }));
      await route.fulfill({ json: versionResponse() });
      return;
    }

    match = path.match(/^\/requerimientos\/(\d+)\/versiones\/(\d+)\/([a-z-]+)$/);
    if (match !== null && method === "POST") {
      const resource = match[3] as CollectionKey;
      const body = JSON.parse(request.postData() ?? "{}") as Record<string, unknown>;
      state.captured.collectionPosts.push({ resource, body });
      const item: Item = {
        id: nextItemId++,
        contenido: String(body.contenido),
        orden: state.collections[resource].length + 1,
        activo: true,
      };
      if (resource === "beneficios") {
        item.tipo = body.tipo === "CUANTITATIVO" ? "CUANTITATIVO" : "CUALITATIVO";
      }
      state.collections[resource] = [...state.collections[resource], item];
      await route.fulfill({ status: 201, json: versionResponse() });
      return;
    }

    match = path.match(/^\/requerimientos\/(\d+)\/versiones\/(\d+)\/([a-z-]+)\/(\d+)$/);
    if (match !== null && method === "PATCH") {
      const resource = match[3] as CollectionKey;
      const itemId = Number(match[4]);
      const body = JSON.parse(request.postData() ?? "{}") as { contenido: string };
      state.collections[resource] = state.collections[resource].map((item) =>
        item.id === itemId ? { ...item, contenido: body.contenido } : item,
      );
      await route.fulfill({ json: versionResponse() });
      return;
    }

    if (match !== null && method === "DELETE") {
      const resource = match[3] as CollectionKey;
      const itemId = Number(match[4]);
      state.collections[resource] = state.collections[resource]
        .filter((item) => item.id !== itemId)
        .map((item, index) => ({ ...item, orden: index + 1 }));
      await route.fulfill({ status: 204, body: "" });
      return;
    }

    await route.fulfill({
      status: 404,
      json: {
        error: {
          code: "not_found",
          message: `Ruta no mockeada: ${method} ${path}`,
          details: null,
        },
      },
    });
  });

  return state;
}
