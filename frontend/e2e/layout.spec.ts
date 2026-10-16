import { expect, test } from "@playwright/test";

import { installBackend } from "./support/backend";
import { openList } from "./support/wizard";

test("muestra el layout base con tipografia y paleta institucional", async ({ page }) => {
  installBackend(page);
  await page.route("**/version", (route) =>
    route.fulfill({ json: { version: "0.1.0-test" } }),
  );
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok", database: "ok" } }),
  );

  await openList(page);

  const header = page.getByRole("banner");
  await expect(header).toBeVisible();
  await expect(header).toContainText("Gestor de Requerimientos");
  await expect(header).toContainText(
    "Especificacion de Requerimientos de Software",
  );

  const fontFamily = await page
    .locator("body")
    .evaluate((el) => getComputedStyle(el).fontFamily);
  expect(fontFamily).toContain("Inter");

  const bodyBackground = await page
    .locator("body")
    .evaluate((el) => getComputedStyle(el).backgroundColor);
  expect(bodyBackground).toBe("rgb(248, 250, 252)");

  const brandBackground = await page
    .getByTestId("brand-badge")
    .evaluate((el) => getComputedStyle(el).backgroundColor);
  expect(brandBackground).toBe("rgb(15, 76, 129)");

  await expect(
    page.getByRole("navigation", { name: "Navegacion principal" }),
  ).toBeVisible();
  await expect(page.getByText("Titulo de prueba")).toBeVisible();
});

test("el boton de estado del sistema muestra la vista de overview", async ({ page }) => {
  installBackend(page);
  await page.route("**/version", (route) =>
    route.fulfill({ json: { version: "0.1.0-test" } }),
  );
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok", database: "ok" } }),
  );

  await openList(page);
  await page.getByRole("button", { name: "Estado del sistema" }).click();

  await expect(
    page.getByRole("heading", { name: "Estado del sistema" }),
  ).toBeVisible();
  await expect(page.getByText("0.1.0-test")).toBeVisible();
  await expect(page.getByText("aplicacion ok")).toBeVisible();
  await expect(page.getByText("base de datos ok")).toBeVisible();
});

test("la barra lateral navega entre secciones", async ({ page }) => {
  installBackend(page);
  await openList(page);

  await page.getByRole("button", { name: "Plantillas ERS/SRS" }).click();
  await expect(
    page.getByRole("heading", { name: "Plantillas ERS/SRS" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Repositorio Documental" }).click();
  await expect(
    page.getByRole("heading", { name: "Repositorio Documental" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Requerimientos" }).click();
  await expect(page.getByRole("heading", { name: "Requerimientos" })).toBeVisible();
});

test("cliente usa rutas relativas /api/v1 (humo de proxy)", async ({ page }) => {
  const backend = installBackend(page);
  backend.total = 1;
  const requests: string[] = [];

  page.on("request", (request) => {
    const url = request.url();
    if (url.includes("/api/v1/")) {
      requests.push(url);
    }
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Requerimientos" })).toBeVisible();

  await expect.poll(() => requests.length > 0).toBe(true);
  expect(requests.every((url) => url.includes("/api/v1/"))).toBe(true);
});
