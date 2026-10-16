import { expect, test } from "@playwright/test";

import { installBackend } from "./support/backend";
import {
  advanceTo,
  createRequirement,
  fillStep1,
  openList,
  openWizard,
} from "./support/wizard";

test("listado: filtros por estado y folio, y paginacion", async ({ page }) => {
  const backend = installBackend(page);
  backend.total = 11;

  await openList(page);

  await expect(page.getByText("Mostrando 1-10 de 11")).toBeVisible();
  await expect(page.getByText("Pagina 1 de 2")).toBeVisible();

  await page.getByLabel("Estado").selectOption("BORRADOR");
  await expect
    .poll(() => backend.captured.listQueries.some((query) => query.includes("estado=BORRADOR")))
    .toBe(true);

  await page.getByLabel("Folio").fill("5");
  await page.getByRole("button", { name: "Filtrar" }).click();
  await expect
    .poll(() => backend.captured.listQueries.some((query) => query.includes("folio=5")))
    .toBe(true);

  await page.getByRole("button", { name: "Siguiente" }).click();
  await expect(page.getByText("Pagina 2 de 2")).toBeVisible();
});

test("paso 1: bloqueo de siguiente hasta crear el requerimiento", async ({ page }) => {
  installBackend(page);
  await openWizard(page);

  await expect(page.getByText("T#", { exact: true })).toBeVisible();
  await expect(page.getByLabel(/^Folio/)).toHaveValue("");
  await expect(page.getByText("Cree el requerimiento para continuar.")).toBeVisible();
  await expect(page.getByText(/^T#/)).toBeVisible();
  await expect(page.getByLabel(/^Folio/)).toHaveValue("");
  const create = page.getByRole("button", { name: "Crear requerimiento" });
  await expect(create).toBeDisabled();

  await fillStep1(page);
  await expect(create).toBeEnabled();
});

test("paso 2: bloqueo por obligatorios con motivo visible", async ({ page }) => {
  installBackend(page);
  await openWizard(page);
  await createRequirement(page);

  await expect(page.getByRole("button", { name: "Siguiente" })).toBeDisabled();
  await expect(page.getByText(/Complete los obligatorios del paso 2/i)).toBeVisible();

  await page.getByLabel("Necesidad actual").fill("Necesidad de prueba");
  await expect(page.getByRole("button", { name: "Siguiente" })).toBeEnabled();
  await expect(page.getByText(/Complete los obligatorios del paso 2/i)).toHaveCount(0);
});

test("paso 1: alta de requerimiento y avance al paso 2", async ({ page }) => {
  const backend = installBackend(page);
  await openWizard(page);
  await createRequirement(page);

  expect(backend.captured.createBodies[0]).toMatchObject({
    folio: 123,
    titulo: "Titulo de prueba",
    tipo_cambio_id: 1,
    sistema: "Sistema X",
    version_documento: "1.0",
    fecha_version: "2026-10-16",
  });

  await page.getByRole("button", { name: "Anterior" }).click();
  await expect(page.getByText("Ticket: T#123")).toBeVisible();
  await expect(page.getByLabel(/^Folio/)).toBeDisabled();
});

test("paso 1: error duplicate_folio se muestra en el paso", async ({ page }) => {
  const backend = installBackend(page);
  backend.createError = {
    status: 409,
    code: "duplicate_folio",
    message: "El folio 123 ya existe.",
  };

  await openWizard(page);
  await fillStep1(page);
  await page.getByRole("button", { name: "Crear requerimiento" }).click();

  await expect(page.getByRole("alert")).toContainText("El folio 123 ya existe.");
  await expect(page.getByRole("heading", { name: "Paso 1: Datos generales" })).toBeVisible();
  await expect(page.getByLabel(/^Folio/)).toHaveValue("123");
  await expect(page.getByLabel("Titulo")).toHaveValue("Titulo de prueba");
});

test("paso 3: colecciones agregan, reordenan, editan y eliminan", async ({ page }) => {
  const backend = installBackend(page);
  await openWizard(page);
  await createRequirement(page);
  await advanceTo(page, 2);

  await page.getByLabel("Nuevo objetivo").fill("Primer objetivo");
  await page.getByRole("button", { name: "Agregar" }).click();
  await expect(page.getByText("Primer objetivo")).toBeVisible();

  await page.getByLabel("Nuevo objetivo").fill("Segundo objetivo");
  await page.getByRole("button", { name: "Agregar" }).click();
  await expect(page.getByText("Segundo objetivo")).toBeVisible();

  const rows = page.locator("li").filter({ hasText: /^#\d+/ });
  await rows
    .filter({ hasText: "Segundo objetivo" })
    .getByRole("button", { name: "Subir" })
    .click();
  await expect(rows.nth(0)).toContainText("Segundo objetivo");

  await rows
    .filter({ hasText: "Primer objetivo" })
    .getByRole("button", { name: "Editar" })
    .click();
  await page.getByLabel(/Editar elemento/).fill("Objetivo editado");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByText("Objetivo editado")).toBeVisible();

  await page
    .getByRole("listitem")
    .filter({ hasText: "Segundo objetivo" })
    .getByRole("button", { name: "Eliminar" })
    .click();
  await expect(page.getByText("Segundo objetivo")).toHaveCount(0);

  expect(backend.captured.collectionPosts.every((post) => post.resource === "objetivos")).toBe(true);
});

test("paso 5: beneficios cualitativos y cuantitativos con su tipo", async ({ page }) => {
  const backend = installBackend(page);
  await openWizard(page);
  await createRequirement(page);
  await advanceTo(page, 4);

  await expect(page.getByRole("heading", { name: "Beneficios cualitativos" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Beneficios cuantitativos" })).toBeVisible();

  const sections = page.locator("section section");
  const cuali = sections.filter({ hasText: "Beneficios cualitativos" });
  const cuanti = sections.filter({ hasText: "Beneficios cuantitativos" });

  await cuali.getByLabel("Nuevo beneficio cualitativos").fill("Mejora de servicio");
  await cuali.getByRole("button", { name: "Agregar" }).click();
  await expect(cuali.getByText("Mejora de servicio")).toBeVisible();
  await expect(cuanti.getByText("Mejora de servicio")).toHaveCount(0);

  await cuanti.getByLabel("Nuevo beneficio cuantitativos").fill("Ahorro del 20%");
  await cuanti.getByRole("button", { name: "Agregar" }).click();
  await expect(cuanti.getByText("Ahorro del 20%")).toBeVisible();

  expect(
    backend.captured.collectionPosts
      .filter((post) => post.resource === "beneficios")
      .map((post) => post.body.tipo),
  ).toEqual(["CUALITATIVO", "CUANTITATIVO"]);
});

test("paso 6: descripcion contextual sin carga de imagenes", async ({ page }) => {
  const backend = installBackend(page);
  await openWizard(page);
  await createRequirement(page);
  await advanceTo(page, 5);

  await expect(
    page.getByText("Este paso no ofrece carga de imagenes ni anexos en esta version."),
  ).toBeVisible();
  await expect(page.locator('input[type="file"]')).toHaveCount(0);

  await page.getByLabel("Descripcion contextual").fill("Contexto modificado");
  await page.getByLabel("Manejo de errores").fill("Errores controlados");

  await expect
    .poll(() =>
      backend.captured.patchBodies.some((body) =>
        "contexto_descripcion" in body || "contexto_manejo_errores" in body,
      ),
    )
    .toBe(true);

  const lastPatch = backend.captured.patchBodies.at(-1) ?? {};
  expect(lastPatch.contexto_descripcion).toBe("Contexto modificado");
  expect(lastPatch.contexto_manejo_errores).toBe("Errores controlados");
});

test("paso 9: toggle no aplica oculta requisitos futuros", async ({ page }) => {
  const backend = installBackend(page);
  await openWizard(page);
  await createRequirement(page);
  await advanceTo(page, 8);

  await expect(page.getByLabel("Descripcion de requisitos futuros")).toBeVisible();
  await expect(page.getByLabel("Nuevo requisito futuro")).toBeVisible();

  await page.getByLabel("No aplica (sin requisitos futuros)").check();

  await expect(page.getByLabel("Descripcion de requisitos futuros")).toHaveCount(0);
  await expect(page.getByLabel("Nuevo requisito futuro")).toHaveCount(0);

  await expect
    .poll(() =>
      backend.captured.patchBodies.some((body) => "requisitos_futuros_aplica" in body),
    )
    .toBe(true);

  const lastPatch = backend.captured.patchBodies.at(-1) ?? {};
  expect(lastPatch.requisitos_futuros_aplica).toBe(false);
});

test("paso 12: control documental sin registro de firmas", async ({ page }) => {
  installBackend(page);
  await openWizard(page);
  await createRequirement(page);
  await advanceTo(page, 11);

  await expect(page.getByRole("heading", { name: "Elaboro" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Reviso" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Autorizo" })).toBeVisible();
  await expect(page.getByLabel("Cargo").first()).toBeVisible();
  await expect(page.getByRole("button", { name: /firmar/i })).toHaveCount(0);
  await expect(
    page.getByText("Este paso es de captura; el registro de firmas se realiza fuera del wizard."),
  ).toBeVisible();
});

test("paso 13: revision resume pasos y permite navegar", async ({ page }) => {
  installBackend(page);
  await openWizard(page);
  await createRequirement(page);
  await advanceTo(page, 12);

  await expect(page.getByText("Paso 1: Datos generales")).toBeVisible();
  await expect(page.getByText("Ticket: T#123")).toBeVisible();

  await page
    .getByRole("listitem")
    .filter({ hasText: "Paso 3: Objetivos generales" })
    .getByRole("button", { name: "Ir al paso" })
    .click();
  await expect(page.getByRole("heading", { name: "Paso 3: Objetivos generales" })).toBeVisible();
});
