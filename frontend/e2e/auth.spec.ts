import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

import { installBackend } from "./support/backend";
import {
  advanceTo,
  createRequirement,
  openList,
  openWizard,
} from "./support/wizard";

async function login(page: Page): Promise<void> {
  const overlay = page.getByTestId("login-overlay");
  await expect(overlay).toBeVisible();
  await page.getByLabel("Usuario").fill("tester");
  await page.getByLabel("Contrasena").fill("secreto123");
  await overlay.getByRole("button", { name: "Ingresar" }).click();
  await expect(overlay).toHaveCount(0);
}

test("sin sesion muestra el overlay de login y permite entrar", async ({ page }) => {
  installBackend(page, { authenticated: false });

  await page.goto("/");
  await expect(page.getByTestId("login-overlay")).toBeVisible();

  await login(page);
  await expect(page.getByRole("heading", { name: "Requerimientos" })).toBeVisible();
});

test("credenciales invalidas muestran un mensaje legible", async ({ page }) => {
  const backend = installBackend(page, { authenticated: false });
  backend.loginError = {
    status: 401,
    code: "invalid_credentials",
    message: "Usuario o contrasena incorrectos.",
  };

  await page.goto("/");
  await expect(page.getByTestId("login-overlay")).toBeVisible();
  await page.getByLabel("Usuario").fill("tester");
  await page.getByLabel("Contrasena").fill("mala");
  await page.getByRole("button", { name: "Ingresar" }).click();

  await expect(page.getByRole("alert")).toContainText(
    "Usuario o contrasena incorrectos.",
  );
  await expect(page.getByTestId("login-overlay")).toBeVisible();
});

test("401 simulado abre el overlay y tras re-autenticar conserva el borrador", async ({
  page,
}) => {
  const backend = installBackend(page);
  await openWizard(page);
  await createRequirement(page);

  await page.getByLabel("Necesidad actual").fill("Necesidad persistida");
  await expect
    .poll(() =>
      backend.captured.patchBodies.some(
        (body) => body.necesidad_actual === "Necesidad persistida",
      ),
    )
    .toBe(true);

  backend.unauthorized = true;
  await page.getByLabel("Necesidad actual").fill("Necesidad persistida 2");
  await expect(page.getByTestId("login-overlay")).toBeVisible();

  backend.unauthorized = false;
  await login(page);

  await expect(
    page.getByRole("heading", { name: "Paso 2: Necesidad actual" }),
  ).toBeVisible();
  await expect(page.getByLabel("Necesidad actual")).toHaveValue(
    "Necesidad persistida 2",
  );
});

test("403 muestra acceso denegado sin perder el wizard", async ({ page }) => {
  const backend = installBackend(page, { roles: ["ELABORO", "AUTORIZO"] });
  await openWizard(page);
  await createRequirement(page);
  backend.requirementStatus = "APROBADO";
  await advanceTo(page, 12);

  backend.documentError = {
    status: 403,
    code: "forbidden",
    message: "El usuario no tiene permiso para esta accion.",
  };
  await page.getByRole("button", { name: "Generar DOCX/PDF" }).click();

  await expect(page.getByRole("alert")).toContainText(
    "No tiene permiso para generar documentos.",
  );
  await expect(
    page.getByRole("heading", { name: "Paso 13: Revision" }),
  ).toBeVisible();
  await expect(page.getByText("Ticket: T#123")).toBeVisible();
});

test("la pantalla de usuarios es visible y operable para ADMIN", async ({ page }) => {
  installBackend(page, { roles: ["ADMIN"] });
  await openList(page);

  await page.getByRole("button", { name: "Gestion de usuarios" }).click();
  await expect(
    page.getByRole("heading", { name: "Gestion de usuarios" }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "tester", exact: true }),
  ).toBeVisible();
});

test("un usuario sin ADMIN no ve la gestion de usuarios", async ({ page }) => {
  installBackend(page, { roles: ["ELABORO"] });
  await openList(page);

  await expect(
    page.getByRole("button", { name: "Gestion de usuarios" }),
  ).toHaveCount(0);
});
