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

- Sem chaves externas, o sistema usa respostas simuladas para facilitar desenvolvimento inicial.
- O consumo de créditos está configurado para 1 crédito por lote (3 vídeos).

## Seed e teste client

```bash
python scripts/seed.py
python scripts/client_smoke_test.py
```

Para Railway com CLI já linkado ao projeto:

```bash
railway run python scripts/seed.py
railway run python scripts/client_smoke_test.py
```
