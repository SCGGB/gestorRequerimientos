import { expect, test } from "@playwright/test";

test("muestra el layout base con tipografia y paleta institucional", async ({ page }) => {
  await page.route("**/version", (route) =>
    route.fulfill({ json: { version: "0.1.0-test" } }),
  );
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok", database: "ok" } }),
  );

  await page.goto("/");

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
    page.getByRole("heading", { name: "Estado del sistema" }),
  ).toBeVisible();
  await expect(page.getByText("0.1.0-test")).toBeVisible();
  await expect(page.getByText("aplicacion ok")).toBeVisible();
  await expect(page.getByText("base de datos ok")).toBeVisible();
});