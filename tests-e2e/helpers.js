const { expect } = require('@playwright/test');

async function registerAndLogin(page, email) {
  await page.goto('/register');
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill('senha123');
  await page.getByRole('button', { name: 'Criar conta' }).click();

  await expect(page).toHaveURL(/\/login$/);

  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill('senha123');
  await page.getByRole('button', { name: 'Acessar painel' }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
}

async function loginAsAdmin(page) {
  await page.goto('/login');
  await page.locator('input[name="email"]').fill('admin@agentesia.com');
  await page.locator('input[name="password"]').fill('admin123');
  await page.getByRole('button', { name: 'Acessar painel' }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
}

module.exports = {
  loginAsAdmin,
  registerAndLogin,
};