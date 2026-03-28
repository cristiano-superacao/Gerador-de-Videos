# Agentes IA Studio

Plataforma modular com FastAPI para:

- ingestão de conteúdo (tema/link/vídeo)
- pesquisa profunda (Tavily/Perplexity)
- geração de 3 roteiros
- criação de vídeos (Shotstack)
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
2. Adicione PostgreSQL e copie a `DATABASE_URL`.
3. Configure variáveis no painel:
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - `TAVILY_API_KEY` ou `PERPLEXITY_API_KEY`
   - `SHOTSTACK_API_KEY`
   - `SHOTSTACK_OWNER_ID`
   - `SECRET_KEY`
4. Faça deploy com Dockerfile da raiz.

## Observações

- **Modo Demonstração**: Sem as chaves da API do Shotstack (`SHOTSTACK_API_KEY` e `SHOTSTACK_OWNER_ID`), o sistema funciona em modo demonstração com vídeos de exemplo. Para gerar vídeos reais customizados, configure as chaves seguindo as instruções no arquivo `.env.example`.
- **Visualização e Download**: No dashboard, você pode visualizar e baixar os vídeos gerados clicando nos botões "Visualizar" e "Baixar" na coluna "Saída".
- Sem chaves externas de IA (OpenAI, Tavily, Perplexity), o sistema usa respostas simuladas para facilitar desenvolvimento inicial.
- O consumo de créditos está configurado para 1 crédito por lote (3 vídeos).

## Seed e teste client

```bash
python scripts/seed.py
python scripts/client_smoke_test.py
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
set EXTERNAL_API_SMOKE_ALLOW_SHOTSTACK_RENDER=1
python scripts/external_api_smoke.py
```

No GitHub Actions, o smoke externo só roda se os secrets abaixo estiverem definidos:

- `RUN_EXTERNAL_API_SMOKE`
- `EXTERNAL_API_SMOKE_ALLOW_SHOTSTACK_RENDER`
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `PERPLEXITY_API_KEY`
- `SHOTSTACK_API_KEY`
- `SHOTSTACK_OWNER_ID`

## Git local e publicação

Para este projeto, o repositório local pode ser inicializado com:

```bash
git init -b main
git add .
git commit -m "chore: preparar projeto"
```

Depois disso, basta conectar um remote e publicar normalmente.
Se quiser apenas preparar o ambiente, o arquivo `.env` pode ser criado com base em `.env.example`.
