# Configuração de Geração de Vídeos

## Modo Demonstração vs Modo Real

Este sistema possui dois modos de operação:

### 🎬 Modo Demonstração (Atual)
- **Ativo quando**: As chaves do Shotstack não estão configuradas
- **Comportamento**: Exibe vídeos de exemplo pré-gerados
- **Indicação**: Badge amarelo "⚠️ Modo Demonstração" e ícone 📹 nos jobs
- **Vantagem**: Permite testar a interface sem custos

### ✨ Modo Real
- **Ativo quando**: As chaves do Shotstack estão configuradas
- **Comportamento**: Gera vídeos personalizados com base nos roteiros criados
- **Custo**: Consulte os planos em [shotstack.io/pricing](https://shotstack.io/pricing)
- **Plano gratuito**: 20 renderizações por mês

## Como Configurar o Shotstack

### Passo 1: Criar Conta

1. Acesse: https://dashboard.shotstack.io/register
2. Preencha o formulário de cadastro
3. Confirme seu e-mail
4. Faça login no dashboard

### Passo 2: Obter API Key

1. No dashboard do Shotstack, clique em **"API Keys"** no menu lateral
2. Você verá sua chave de API (começa com `sk_test_` ou `sk_prod_`)
3. Clique em **"Copy"** para copiar a chave
4. **Importante**: Guarde esta chave em local seguro. Por segurança, ela só é exibida uma vez.

### Passo 3: Obter Owner ID

1. Ainda no dashboard, clique em **"Settings"** (Configurações)
2. Procure por **"Owner ID"** ou **"Account ID"**
3. Copie o ID (geralmente é uma string alfanumérica)

### Passo 4: Configurar no Sistema

#### Desenvolvimento Local (.env)

1. Abra o arquivo `.env` na raiz do projeto (crie copiando `.env.example` se não existir):
   ```bash
   copy .env.example .env
   ```

2. Adicione suas chaves:
   ```env
   SHOTSTACK_API_KEY=sk_test_sua_chave_aqui
   SHOTSTACK_OWNER_ID=seu_owner_id_aqui
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
   - `SHOTSTACK_OWNER_ID`: seu owner ID
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

**Causa**: As chaves não foram configuradas corretamente ou o servidor não foi reiniciado.

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

Para mais informações, consulte a documentação oficial: https://shotstack.io/docs/guide/getting-started/
