const { test, expect } = require('@playwright/test');
const { registerAndLogin } = require('./helpers');

test.use({ viewport: { width: 390, height: 844 } });

test('dashboard permanece utilizavel em viewport mobile', async ({ page }) => {
  const uniqueEmail = `playwright.mobile.${Date.now()}@example.com`;

  await registerAndLogin(page, uniqueEmail);

  await expect(page.getByRole('heading', { name: 'Painel de Produção' })).toBeVisible();
  await expect(page.getByText(`Usuário: ${uniqueEmail}`)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Gerar 3 roteiros e vídeos' })).toBeVisible();

  await page.locator('#source_type').selectOption('video');
  await expect(page.locator('#source_file_group')).toBeVisible();
  await expect(page.locator('#source_file')).toBeVisible();

  await page.locator('#source_type').selectOption('text');
  await expect(page.locator('#source_file_group')).toBeHidden();
  await expect(page.locator('#source_content')).toBeVisible();
});