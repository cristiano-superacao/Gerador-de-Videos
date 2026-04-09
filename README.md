# Agentes IA Studio

Plataforma modular com FastAPI para:

- ingestão de conteúdo (tema/link/vídeo)
- pesquisa profunda (Tavily/Perplexity)
- geração de 3 roteiros
- criação de vídeos (Shotstack)
- criação de vídeos com Shotstack ou Veo (Gemini API)
- painel admin com controle de créditos

## Estrutura

```text
app/
  core/
  models/
  routes/
  services/
  templates/
static/
main.py
Dockerfile
requirements.txt
```

## Rodando localmente

> Importante: este projeto é Python (FastAPI) e não usa Node/NPM para build do front. Se você tentou `npm rum dev` (além do typo em "rum"), verá erro de `package.json` inexistente. Use os comandos abaixo.

1. Crie e ative um ambiente virtual.
1. Instale dependências:

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
```

1. Copie variáveis:

```bash
copy .env.example .env
```

1. Suba a aplicação:

```bash
python -m uvicorn main:app --reload
```

Opcional (para quem prefere `npm run dev`): adicionamos um `package.json` com scripts que chamam o Python da venv. Após criar a venv e instalar os requisitos, você pode usar:

```bash
npm run dev
```

Caso receba erro ao usar `npm run dev`, verifique se a venv `.venv` existe e se o Windows está permitindo execução de scripts.
Acesse:

- Home: <http://localhost:8000/>
- Guia de uso: <http://localhost:8000/como-usar>
- Login: <http://localhost:8000/login>
- Admin inicial: `admin@agentesia.com` / `admin123`

## Railway

1. Crie um projeto no Railway.
1. Adicione PostgreSQL e copie a `DATABASE_URL`.

1. Configure estas variáveis no painel: `DATABASE_URL`, `OPENAI_API_KEY`, `TAVILY_API_KEY` ou `PERPLEXITY_API_KEY`, `SECRET_KEY` e uma destas opções de provider:

- `VIDEO_PROVIDER=shotstack`, `SHOTSTACK_API_KEY`, `SHOTSTACK_OWNER_ID` (opcional), `SHOTSTACK_ENV` (`stage` ou `production`)
- `VIDEO_PROVIDER=veo`, `GEMINI_API_KEY`, `VEO_MODEL` (opcional), `VEO_ASPECT_RATIO` (opcional), `VEO_RESOLUTION` (opcional), `VEO_DURATION_SECONDS` (opcional) e `GEMINI_IMAGE_MODEL` (opcional)

1. Faça deploy com Dockerfile da raiz.

## Observações

- **Modo Demonstração**: Sem as credenciais do provider ativo, o sistema funciona em modo demonstração.
- **Veo sem login e senha**: a integração com Veo usa `GEMINI_API_KEY` da Gemini API, não credenciais interativas de usuário.
- **Imagem-guia no Veo**: com `VIDEO_PROVIDER=veo`, o sistema cria uma imagem vertical a partir do roteiro antes de iniciar a geração do vídeo.
- **Fallback automático**: se `VIDEO_PROVIDER=veo` e a Gemini API recusar o render por quota esgotada, o sistema tenta reenviar automaticamente ao Shotstack quando `SHOTSTACK_API_KEY` estiver configurada.
- **Visualização e Download**: No dashboard, você pode visualizar e baixar os vídeos gerados clicando nos botões "Visualizar" e "Baixar" na coluna "Saída".
- **Histórico operacional por job**: o dashboard registra provider solicitado, provider executado e a mensagem operacional retornada pelo provider, incluindo quota do Veo e fallback para Shotstack.
- Sem chaves externas de IA (OpenAI, Tavily, Perplexity), o sistema usa respostas simuladas para facilitar desenvolvimento inicial.
- O consumo de créditos está configurado para 1 crédito por lote (3 vídeos).

## Seed e teste client

```bash
python scripts/seed.py
python scripts/client_smoke_test.py
python scripts/system_validation.py
pytest
```

Para validar a instância publicada com o mesmo client smoke:

```bash
set APP_BASE_URL=https://api-production-fb1e.up.railway.app
python scripts/client_smoke_test.py
```

Para Railway com CLI já linkado ao projeto:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\railway_seed_and_smoke.ps1
```

O script usa a `DATABASE_PUBLIC_URL` do serviço Postgres para semear o banco remoto
e depois executa o mesmo `client_smoke_test.py` contra a URL pública do serviço `api`.

Para validar todas as funcionalidades diretamente no Railway, incluindo E2E desktop e mobile:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\railway_full_validation.ps1
```

## Testes automatizados

Os testes em pytest usam banco SQLite isolado por execução e validam autenticação,
geração e administração sem depender do smoke test manual.

Para validar a interface do dashboard no navegador:

```bash
npm install
npm run install:browsers
npm run test:e2e
```

Para um teste rápido de responsividade mobile do dashboard:

```bash
npm run test:e2e:mobile
```

O CI em [.github/workflows/python-app.yml](.github/workflows/python-app.yml) executa:

```bash
python -m pytest tests -q
npm run test:e2e
```

Existe tambem um workflow dedicado para validar a instancia publicada no Railway em
[.github/workflows/railway-production-validation.yml](.github/workflows/railway-production-validation.yml).
Ele roda seed remoto, smoke HTTP, E2E desktop e E2E mobile diretamente contra a URL publica,
desde que a variável `PRODUCTION_BASE_URL` esteja configurada no GitHub Actions.

Os workflows legados de `Pylint` e `Python Package using Conda` foram removidos porque
duplicavam o pipeline principal e falhavam sem agregar cobertura útil ao projeto atual.

## Smoke de APIs externas

Use o smoke controlado abaixo apenas em ambiente com credenciais reais configuradas:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\run_external_smoke.ps1
```

O script valida as variáveis obrigatórias antes de executar o smoke. Se preferir rodar manualmente:

```bash
set RUN_EXTERNAL_API_SMOKE=1
python scripts/external_api_smoke.py
```

Para permitir um render real no Shotstack durante o smoke:

```bash
set SHOTSTACK_ENV=production
set EXTERNAL_API_SMOKE_ALLOW_SHOTSTACK_RENDER=1
python scripts/external_api_smoke.py
```

Para permitir um render real no Veo durante o smoke:

```bash
set VIDEO_PROVIDER=veo
set GEMINI_API_KEY=AIza...
set EXTERNAL_API_SMOKE_ALLOW_VEO_RENDER=1
python scripts/external_api_smoke.py
```

Para configurar isso localmente sem editar o `.env` manualmente:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\configure_gemini_key.ps1
```

Para preparar o fallback local para Shotstack sem alterar o provider ativo manualmente:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\configure_shotstack_fallback.ps1
```

Se preferir usar o arquivo .env, basta preencher GEMINI_API_KEY, ajustar VIDEO_PROVIDER=veo e executar o wrapper:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\run_external_smoke.ps1
```

O smoke agora carrega automaticamente o .env, respeita o provider ativo e faz polling até o render terminar. Opcionalmente, você pode controlar o tempo com:

- EXTERNAL_API_SMOKE_RENDER_TIMEOUT
- EXTERNAL_API_SMOKE_POLL_INTERVAL

No GitHub Actions, o smoke externo só roda se os secrets abaixo estiverem definidos:

- `RUN_EXTERNAL_API_SMOKE`
- `EXTERNAL_API_SMOKE_ALLOW_SHOTSTACK_RENDER`
- `EXTERNAL_API_SMOKE_ALLOW_VEO_RENDER`
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `PERPLEXITY_API_KEY`
- `SHOTSTACK_API_KEY`
- `GEMINI_API_KEY`

Se o smoke retornar `429 RESOURCE_EXHAUSTED` com Veo, o problema está na quota ou no faturamento da Gemini API, não no fluxo interno do projeto. Nesse caso:

1. Revise quota e billing em `https://ai.dev/projects`.
2. Revise consumo atual em `https://ai.dev/rate-limit`.
3. Se quiser continuidade operacional enquanto ajusta a conta Gemini, configure `SHOTSTACK_API_KEY` para liberar o fallback automático.

## Git local e publicação

Para este projeto, o repositório local pode ser inicializado com:

```bash
git init -b main
git add .
git commit -m "chore: preparar projeto"
```

Depois disso, basta conectar um remote e publicar normalmente.
Se quiser apenas preparar o ambiente, o arquivo `.env` pode ser criado com base em `.env.example`.
