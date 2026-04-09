# Configuração de Geração de Vídeos

## Modo Demonstração vs Modo Real

Este sistema possui dois modos de operação:

## Providers disponíveis

- `shotstack`: fluxo atual de renderização por timeline.
- `veo`: gera imagem-guia com Gemini Image e vídeo com Veo 3.1 via Gemini API.

## Fallback automático Veo -> Shotstack

Quando `VIDEO_PROVIDER=veo`, o sistema tenta usar Veo como provider principal.
Se a Gemini API devolver quota esgotada ou limite de uso e `SHOTSTACK_API_KEY`
estiver configurada, o render é reenviado automaticamente ao Shotstack.

No dashboard e na página de resultado, cada job passa a mostrar:

- provider solicitado
- provider executado
- mensagem operacional do provider

Isso permite ver claramente quando o Veo falhou por quota e quando o Shotstack
assumiu o render como fallback.

O provider é controlado por `VIDEO_PROVIDER`. Para Veo, o sistema usa chave de API (`GEMINI_API_KEY`) e não login/senha interativos.

### 🎬 Modo Demonstração (Atual)

- **Ativo quando**: A API Key do Shotstack não está configurada
- **Comportamento**: Exibe vídeos de exemplo pré-gerados
- **Indicação**: Badge amarelo "⚠️ Modo Demonstração" e ícone 📹 nos jobs
- **Vantagem**: Permite testar a interface sem custos

### ✨ Modo Real

- **Ativo quando**: As credenciais do provider ativo estão configuradas
- **Comportamento**: Gera vídeos personalizados com base nos roteiros criados
- **Custo**: Consulte os planos em [shotstack.io/pricing](https://shotstack.io/pricing)
- **Plano gratuito**: 20 renderizações por mês

## Como Configurar o Veo

### Passo 1: Gerar API Key da Gemini

1. Acesse: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Gere uma chave para a Gemini API
3. Guarde a chave com segurança

### Passo 2: Configurar no sistema

#### Desenvolvimento Local (.env)

```env
VIDEO_PROVIDER=veo
GEMINI_API_KEY=sua_chave_aqui
VEO_MODEL=veo-3.1-generate-preview
VEO_ASPECT_RATIO=9:16
VEO_RESOLUTION=720p
VEO_DURATION_SECONDS=8
GEMINI_IMAGE_MODEL=gemini-3.1-flash-image-preview
SHOTSTACK_API_KEY=sk_test_sua_chave_aqui
```

#### Produção

Configure as mesmas variáveis no painel do provedor de hospedagem e reinicie o serviço.

### Como o fluxo Veo funciona

1. O sistema gera 3 roteiros.
2. Para cada roteiro, cria uma imagem-guia vertical.
3. Envia o prompt do roteiro e a imagem para o Veo.
4. Faz polling assíncrono até o vídeo ficar pronto.
5. Baixa o mp4 gerado para o app e publica o link no dashboard.

### Smoke real do Veo

Para configurar a chave local com prompt seguro, use:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\configure_gemini_key.ps1
```

Esse script cria `.env` a partir de `.env.example` se necessário, grava `GEMINI_API_KEY`, troca `VIDEO_PROVIDER=veo` e habilita `EXTERNAL_API_SMOKE_ALLOW_VEO_RENDER=1`.

Para configurar apenas o fallback local com Shotstack, use:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\configure_shotstack_fallback.ps1
```

Depois de preencher o `.env` com `VIDEO_PROVIDER=veo` e `GEMINI_API_KEY`, rode:

```bash
set RUN_EXTERNAL_API_SMOKE=1
set EXTERNAL_API_SMOKE_ALLOW_VEO_RENDER=1
python scripts/external_api_smoke.py
```

Ou use o wrapper:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\run_external_smoke.ps1
```

O smoke carrega o `.env`, cria imagem-guia, envia o render ao Veo e faz polling até concluir. Se precisar aumentar o tempo de espera:

```bash
set EXTERNAL_API_SMOKE_RENDER_TIMEOUT=600
set EXTERNAL_API_SMOKE_POLL_INTERVAL=20
```

Se o smoke retornar `429 RESOURCE_EXHAUSTED`, a aplicação já está alcançando a
Gemini API corretamente. Nesse caso, o bloqueio é de quota/faturamento da conta.
Revise:

- [ai.dev/projects](https://ai.dev/projects)
- [ai.dev/rate-limit](https://ai.dev/rate-limit)

## Como Configurar o Shotstack

### Passo 1: Criar Conta

1. Acesse: [dashboard.shotstack.io/register](https://dashboard.shotstack.io/register)
2. Preencha o formulário de cadastro
3. Confirme seu e-mail
4. Faça login no dashboard

### Passo 2: Obter API Key

1. No dashboard do Shotstack, clique em **"API Keys"** no menu lateral
2. Você verá sua chave de API (começa com `sk_test_` ou `sk_prod_`)
3. Clique em **"Copy"** para copiar a chave
4. **Importante**: Guarde esta chave em local seguro. Por segurança, ela só é exibida uma vez.

### Passo 3: Owner ID Opcional

Use este passo apenas se você for trabalhar com templates que dependem de merge fields.

1. Ainda no dashboard, clique em **"Settings"** (Configurações)
2. Procure por **"Owner ID"** ou **"Account ID"**
3. Copie o ID (geralmente é uma string alfanumérica)

### Passo 4: Configurar no Sistema

#### Desenvolvimento Local (Shotstack)

1. Abra o arquivo `.env` na raiz do projeto (crie copiando `.env.example` se não existir):

   ```bash
   copy .env.example .env
   ```

2. Adicione suas chaves:

   ```env
   SHOTSTACK_API_KEY=sk_test_sua_chave_aqui
   # Opcional
   SHOTSTACK_OWNER_ID=seu_owner_id_aqui
   SHOTSTACK_ENV=stage
   ```

3. Reinicie o servidor:

   ```bash
   # Pare o servidor (Ctrl+C) e reinicie:
   python -m uvicorn main:app --reload
   ```

#### Produção (Railway/Docker)

1. Acesse o painel de configuração do seu serviço
2. Adicione as variáveis de ambiente:
   - `SHOTSTACK_API_KEY`: sua chave de API
   - `SHOTSTACK_OWNER_ID`: opcional, apenas para templates com merge
   - `SHOTSTACK_ENV`: use `stage` para sandbox e `production` para chaves live
3. Reinicie o serviço

## Verificando se Está Funcionando

Após configurar, gere novos vídeos no sistema:

1. Acesse o **Dashboard**
2. Crie uma nova geração de vídeos
3. Observe a tabela "Últimas Gerações":
   - ✅ **Modo Real ativo**: Status será "queued" → "rendering" → "done"
   - ❌ **Ainda em demonstração**: Status será "simulado" com ícone 📹

## Funcionalidades de Visualização

Na coluna "Saída" da tabela de gerações, você encontrará:

- **Visualizar**: Abre o vídeo em uma nova aba do navegador
- **Baixar**: Faz download do vídeo MP4 para seu computador

Ambas as funcionalidades funcionam tanto em modo demonstração quanto em modo real.

## Solução de Problemas

### Vídeos permanecem em modo "simulado"

**Causa**: A API Key não foi configurada corretamente ou o servidor não foi reiniciado.

**Solução**:

1. Verifique se as chaves estão no arquivo `.env` (sem aspas extras)
2. Certifique-se de que não há espaços antes ou depois das chaves
3. Reinicie completamente o servidor
4. Limpe o cache do navegador (Ctrl+Shift+R)

### Erro "401 Unauthorized" nos logs

**Causa**: A API Key do Shotstack está incorreta ou expirou.

**Solução**:

1. Verifique se copiou a chave completa (incluindo o prefixo `sk_`)
2. Gere uma nova chave no dashboard do Shotstack
3. Atualize o `.env` com a nova chave

### Vídeos ficam em "queued" indefinidamente

**Causa**: Problema de comunicação com a API ou limite de plano atingido.

**Solução**:

1. Verifique seu plano no dashboard do Shotstack
2. Confirme se não atingiu o limite mensal de renderizações
3. Aguarde alguns minutos - renderizações podem levar tempo
4. Verifique os logs do servidor para mensagens de erro

## Limites e Considerações

- **Plano Gratuito**: 20 vídeos/mês
- **Tempo de Renderização**: 30 segundos a 3 minutos por vídeo
- **Formato de Saída**: MP4, HD (1280x720), 30fps
- **Duração**: Os vídeos gerados têm ~20 segundos

Para mais informações, consulte a documentação oficial: [shotstack.io/docs/guide/getting-started](https://shotstack.io/docs/guide/getting-started/)
