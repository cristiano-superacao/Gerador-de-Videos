const { test, expect } = require('@playwright/test');
const { loginAsAdmin, registerAndLogin } = require('./helpers');

test('admin ajusta creditos de usuario pela interface', async ({ page }) => {
  const uniqueEmail = `playwright.admin.${Date.now()}@example.com`;

  await registerAndLogin(page, uniqueEmail);
  await page.goto('/');

  await loginAsAdmin(page);
  await page.getByRole('link', { name: 'Gerenciar usuários' }).click();

  await expect(
    page.getByRole('heading', { name: 'Administração de Usuários' })
  ).toBeVisible();

  const userRow = page.locator('tr', { hasText: uniqueEmail });
  await expect(userRow).toBeVisible();
  await userRow.locator('input[name="credits"]').fill('42');
  await userRow.getByRole('button', { name: 'Salvar' }).click();

  await expect(userRow.locator('input[name="credits"]')).toHaveValue('42');
});