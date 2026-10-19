/*
 * Helpers de navegacion del wizard para pruebas e2e (SPEC-004, T-19).
 */

import { expect } from "@playwright/test";
import type { Page } from "@playwright/test";

export async function openList(page: Page): Promise<void> {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Requerimientos" })).toBeVisible();
}

export async function openWizard(page: Page): Promise<void> {
  await page.goto("/");
  await page.getByRole("button", { name: "Nuevo", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Paso 1: Datos generales" })).toBeVisible();
}

export async function fillStep1(page: Page, folio = 123): Promise<void> {
  await page.getByLabel(/^Folio/).fill(String(folio));
  await page.getByLabel("Titulo").fill("Titulo de prueba");
  await page.getByLabel("Tipo de cambio").selectOption("1");
  await page.getByLabel("Sistema").fill("Sistema X");
  await page.getByLabel("Version documental").fill("1.0");
  await page.getByLabel("Fecha de version").fill("2026-10-16");
}

export async function createRequirement(page: Page, folio = 123): Promise<void> {
  await fillStep1(page, folio);
  await page.getByRole("button", { name: "Crear requerimiento" }).click();
  await expect(page.getByRole("heading", { name: "Paso 2: Necesidad actual" })).toBeVisible();
}

async function addCollectionItem(page: Page, inputLabel: string): Promise<void> {
  await page.getByLabel(inputLabel).fill("Elemento de prueba");
  await page.getByRole("button", { name: "Agregar" }).first().click();
  await expect(page.getByText("Elemento de prueba")).toBeVisible();
}

async function completeStep(page: Page, index: number): Promise<void> {
  switch (index) {
    case 1:
      await page.getByLabel("Necesidad actual").fill("Necesidad de prueba");
      break;
    case 2:
      await addCollectionItem(page, "Nuevo objetivo");
      break;
    case 3:
      await addCollectionItem(page, "Nueva consideracion");
      break;
    case 4:
      await addCollectionItem(page, "Nuevo beneficio cualitativos");
      break;
    case 5:
      await page.getByLabel("Descripcion contextual").fill("Contexto de prueba");
      break;
    case 6:
      await page.getByLabel("Usuarios y permisos").fill("Usuarios de prueba");
      break;
    case 7:
      await addCollectionItem(page, "Nueva restriccion");
      break;
    case 8:
      await page
        .getByLabel("Descripcion de requisitos futuros")
        .fill("Requisitos futuros de prueba");
      break;
    case 9:
      await addCollectionItem(page, "Nuevo elemento de volumetria");
      break;
    case 10:
      await addCollectionItem(page, "Nuevo riesgo");
      break;
    case 11: {
      const nombres = page.getByLabel("Nombre");
      await nombres.nth(0).fill("Ana Elaboro");
      await nombres.nth(2).fill("Beto Autorizo");
      break;
    }
  }
}

/** Parte del paso 2 (tras crear) y avanza hasta dejar el paso objetivo activo. */
export async function advanceTo(page: Page, targetIndex: number): Promise<void> {
  for (let index = 1; index < targetIndex; index += 1) {
    await completeStep(page, index);
    await page.getByRole("button", { name: "Siguiente" }).click();
  }
  await expect(
    page.getByRole("heading", { name: new RegExp(`Paso ${targetIndex + 1}:`) }),
  ).toBeVisible();
}
