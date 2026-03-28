const { test, expect } = require('@playwright/test');
const { registerAndLogin } = require('./helpers');

test('dashboard alterna input de video e valida arquivo no cliente', async ({ page }) => {
  const uniqueEmail = `playwright.${Date.now()}@example.com`;

  await registerAndLogin(page, uniqueEmail);
  await expect(page.getByRole('heading', { name: 'Painel de Produção' })).toBeVisible();
  await expect(page.locator('#source_file_group')).toBeHidden();

  await page.locator('#source_type').selectOption('video');

  await expect(page.locator('#source_file_group')).toBeVisible();
  await expect(page.locator('#source_file')).toHaveAttribute('required', '');
  await expect(
    page.locator('#source_content').evaluate((element) => element.required)
  ).resolves.toBe(false);

  await page.locator('#source_file').setInputFiles({
    name: 'documento.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('conteudo invalido'),
  });
  await page.getByRole('button', { name: 'Gerar 3 roteiros e vídeos' }).click();

  await expect(page.locator('#client_error')).toContainText(
    'Formato inválido. Use mp4, mov, mkv, webm, mp3, wav, m4a ou aac.'
  );
});

test('dashboard gera roteiros por texto e mostra tela de resultado', async ({ page }) => {
  const uniqueEmail = `playwright.text.${Date.now()}@example.com`;

  await registerAndLogin(page, uniqueEmail);

  await page.locator('#source_type').selectOption('text');
  await page.locator('#source_content').fill(
    'Tendências de IA para pequenas empresas em 2026'
  );
  await page.getByRole('button', { name: 'Gerar 3 roteiros e vídeos' }).click();

  await expect(page.getByRole('heading', { name: 'Resultado da Geração' })).toBeVisible();
  await expect(page.getByText('Vídeo 1')).toBeVisible();
  await expect(
    page.getByText('Configure SHOTSTACK_API_KEY e SHOTSTACK_OWNER_ID')
  ).toHaveCount(3);
});

test('dashboard aceita upload valido de audio e mostra tela de resultado', async ({ page }) => {
  const uniqueEmail = `playwright.video.${Date.now()}@example.com`;

  await registerAndLogin(page, uniqueEmail);

  await page.locator('#source_type').selectOption('video');
  await page.locator('#source_file').setInputFiles({
    name: 'entrevista.mp3',
    mimeType: 'audio/mpeg',
    buffer: Buffer.from('audio fake content'),
  });
  await page.getByRole('button', { name: 'Gerar 3 roteiros e vídeos' }).click();

  await expect(
    page.getByRole('heading', { name: 'Resultado da Geração' })
  ).toBeVisible();
  await expect(page.getByText('Vídeo 1')).toBeVisible();
  await expect(page.getByText('Vídeo 2')).toBeVisible();
  await expect(page.getByText('Vídeo 3')).toBeVisible();
});

test('dashboard aplica html retornado pelo polling live', async ({ page }) => {
  const uniqueEmail = `playwright.poll.${Date.now()}@example.com`;

  await page.route('**/dashboard/jobs/live', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        jobs: [
          {
            id: 91,
            script_variant: 2,
            status: 'simulado',
            provider: 'shotstack',
            output_url: 'https://cdn.example.com/video-final.mp4',
            created_at: '28/03/2026 10:15',
          },
        ],
        html: `
          <tr class="border-b border-slate-900/80">
            <td class="py-2">91</td>
            <td class="py-2">2</td>
            <td class="py-2">
              <span class="badge badge-info">simulado</span>
              <span class="text-xs text-yellow-400 ml-2" title="Vídeo de demonstração">📹</span>
            </td>
            <td class="py-2">shotstack</td>
            <td class="py-2">
              <div class="flex gap-2">
                <a href="https://cdn.example.com/video-final.mp4" target="_blank" rel="noopener noreferrer" class="text-indigo-300 hover:text-indigo-200" title="Visualizar vídeo">Visualizar</a>
                <span class="text-slate-600">|</span>
                <a href="https://cdn.example.com/video-final.mp4" download class="text-green-300 hover:text-green-200" title="Baixar vídeo">Baixar</a>
              </div>
            </td>
            <td class="py-2">28/03/2026 10:15</td>
          </tr>
        `,
        has_demo_mode: true,
      }),
    });
  });

  await registerAndLogin(page, uniqueEmail);

  await expect(page.locator('#jobs_table_body')).toContainText('91');
  await expect(page.locator('#jobs_table_body')).toContainText('Visualizar');
  await expect(page.locator('#demo_mode_badge')).toBeVisible();
});