# 🍻 Boteco AI

> O bot de WhatsApp que virou membro do grupo.

DJ, fábrica de figurinhas, gerador de imagens com IA, enquetes, previsão do tempo e um papo afiado — tudo num único container Docker.

---

## ✨ Funcionalidades

### 🎵 DJ do Zap
Busca no YouTube, baixa o áudio via `yt-dlp` e envia como **bolinha de voz nativa** do WhatsApp. Suporta fila de músicas com lock atômico no Redis — zero conflito entre pedidos simultâneos.

```
!play bohemian rhapsody
!fila
!limpar
```

### 🖼️ Fábrica de Figurinhas
Converte qualquer imagem em sticker `.webp` 512×512 instantaneamente com **Pillow**. Funciona com foto enviada diretamente ou em reply a uma foto existente.

```
!s          ← junto com uma foto, ou em reply a uma foto
!figurinha  ← mesmo comando, nome alternativo
```

### 🧠 Chat com IA
Alimentado pelo **Groq (Llama 3.3 70B)** (vc pode testar o gemini e deepseek nos providers) com memória de curto prazo via Redis. O bot lembra das últimas mensagens da conversa e responde com a personalidade do Boteco — descontraído, zoeiro, nunca corporativo.

```
!bot qual a capital da França?
!bot me conta uma piada de programação
!ai o que é recursão?
```

> ℹ️ A IA **não responde a mensagens aleatórias** — só é ativada com `!bot`, `!ai` ou `!boteco`.

### 🎨 Geração de Imagens
Gera imagens com IA via **Pollinations.ai** — 100% grátis, sem API key, sem limite.

```
!imagine um cachorro astronauta pilotando uma nave espacial
!img pôr do sol cyberpunk no Rio de Janeiro
```

### 🌤️ Previsão do Tempo
Consulta o clima via **wttr.in** — grátis, sem API key.

```
!clima São Luís
!tempo Tokyo
```

### 🗳️ Enquetes Nativas
Cria enquetes nativas do WhatsApp (com votação real) diretamente no grupo.

```
!enquete "Melhor dia pra churrasco?" Sexta Sábado Domingo
!poll "Qual filme assistir?" Terror Comédia Ação
```

### 📣 Mencionar Todos
Marca todos os membros do grupo numa única mensagem.

```
!todos Galera, reunião às 19h!
!all
```

### 🔗 Link de Convite
Gera o link de convite do grupo (bot precisa ser admin).

```
!link
!convite
```

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| API & Webhook | **FastAPI** |
| Processamento assíncrono | **Celery 5** + **Redis** |
| Fila de mensagens | **Redis** (DB 1 = app, DB 2 = Celery broker) |
| WhatsApp | **Evolution API v2.3** (Baileys) |
| IA / LLM | **Groq API** — Llama 3.3 70B |
| Download de áudio | **yt-dlp** + **FFmpeg** |
| Processamento de imagem | **Pillow** |
| HTTP client | **httpx** (async) |
| Geração de imagens | **Pollinations.ai** (grátis) |
| Clima | **wttr.in** (grátis) |
| Linguagem | **Python 3.11+** |

---

## 📁 Estrutura do Projeto

```
boteco-ai/
├── src/
│   ├── agent/
│   │   ├── core.py           # Orquestrador da IA + memória
│   │   ├── prompts.py        # Personalidade do bot
│   │   └── validator.py      # Limpa respostas corporativas da IA
│   ├── application/
│   │   ├── handle_webhook.py # Recebe eventos da Evolution API
│   │   ├── handle_message.py # Roteia e executa comandos
│   │   └── tasks.py          # Tasks Celery (DJ, figurinha)
│   ├── domain/
│   │   └── guardrails.py     # Regex router de comandos
│   ├── infrastructure/
│   │   ├── celery_app.py     # Configuração do Celery
│   │   ├── redis_client.py   # Singleton Redis
│   │   └── settings.py       # Variáveis de ambiente (Pydantic)
│   ├── memory/
│   │   ├── playlist_manager.py  # Fila do DJ + lock atômico
│   │   └── working_memory.py    # Histórico de conversa (Redis)
│   ├── middleware/
│   │   └── dev_guard.py      # Validação, deduplicação, whitelist
│   ├── providers/
│   │   └── groq_provider.py  # Integração Groq (Llama)
│   ├── services/
│   │   └── evolution_service.py  # Todos os métodos da Evolution API
│   ├── tools/
│   │   ├── tool_dj.py        # Download e envio de áudio
│   │   └── tool_sticker.py   # Conversão de imagem → sticker webp
│   └── main.py               # Entry point FastAPI
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env
```

---

## 🐳 Como Rodar

### Pré-requisitos

- Docker e Docker Compose instalados
- Uma conta na [Evolution API](https://evolution-api.com) ou instância self-hosted
- API key do [Groq](https://console.groq.com) (gratuito)

### 1. Clone o repositório

```bash
git clone https://github.com/SEU_USUARIO/boteco-ai.git
cd boteco-ai
```

### 2. Configure o `.env`

Copie o exemplo e preencha:

```bash
cp .env.example .env
```

```env
# IA
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMP=0.7
GROQ_MAX_TOKENS=300

# Evolution API
EVOLUTION_BASE_URL=http://evolution-api:8080
EVOLUTION_API_KEY=sua_chave_aqui
EVOLUTION_INSTANCE_NAME=boteco
WHATSAPP_HOOK_URL=http://bot:9000/webhook

# Redis
REDIS_URL=redis://boteco-redis:6379/1
CELERY_BROKER_URL=redis://boteco-redis:6379/2

# Segurança
GRUPO_PERMITIDO=120363000000000000@g.us   # ID do grupo (deixe vazio para aceitar todos)
DEV_MODE=false
DEV_WHITELIST=                             # Ex: 5598999999999,5598888888888

# Logs
LOG_LEVEL=INFO
```

### 3. Suba os containers

```bash
docker compose up -d
```

Isso inicia:
- `boteco-redis` — Redis Stack
- `evolution-api` — Evolution API + PostgreSQL
- `bot` — FastAPI (porta 9000)
- `celery-worker` — Worker para músicas e figurinhas

### 4. Conecte o WhatsApp

Acesse o QR Code da Evolution API:

```
http://localhost:8080
```

Escaneie o QR Code com o WhatsApp no celular. A conexão é mantida pelo Baileys.

### 5. Configure o Webhook

O webhook é configurado automaticamente no startup do bot. Verifique os logs:

```bash
docker compose logs bot --tail=30
```

Você deve ver:
```
✅ Webhook configurado (base64=true) → http://bot:9000/webhook
✅ Settings configurados.
```

### 6. Teste no grupo

Adicione o bot ao grupo, mande `!menu` e veja a magia acontecer. 🍻

---

## ⚙️ Variáveis de Ambiente — Referência Completa

| Variável | Padrão | Descrição |
|---|---|---|
| `GROQ_API_KEY` | — | Chave da API Groq (obrigatório) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Modelo Groq |
| `GROQ_TEMP` | `0.7` | Criatividade da IA (0.0–1.0) |
| `GROQ_MAX_TOKENS` | `300` | Limite de tokens por resposta |
| `EVOLUTION_BASE_URL` | — | URL da Evolution API |
| `EVOLUTION_API_KEY` | — | Chave da Evolution API |
| `EVOLUTION_INSTANCE_NAME` | `default` | Nome da instância |
| `WHATSAPP_HOOK_URL` | — | URL pública do webhook |
| `REDIS_URL` | `redis://boteco-redis:6379/1` | Redis para a app |
| `CELERY_BROKER_URL` | `redis://boteco-redis:6379/2` | Redis para o Celery |
| `GRUPO_PERMITIDO` | `` | JID do grupo oficial (vazio = aceita tudo) |
| `DEV_MODE` | `false` | Restringe a whitelist de números |
| `DEV_WHITELIST` | `` | Números permitidos no dev mode |
| `MAX_HISTORY_MESSAGES` | `10` | Mensagens de histórico para a IA |
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`) |

---

## 🗂️ Referência de Comandos

| Comando | Descrição |
|---|---|
| `!menu` / `!ajuda` | Menu completo do bot |
| `!play [música]` | Toca uma música do YouTube |
| `!fila` | Mostra a fila de músicas |
| `!limpar` | Limpa a fila e libera o DJ |
| `!s` / `!figurinha` | Cria sticker da foto enviada ou em reply |
| `!bot [msg]` | Conversa com a IA |
| `!imagine [desc]` | Gera imagem com IA (Pollinations) |
| `!clima [cidade]` | Previsão do tempo |
| `!enquete "P" op1 op2` | Cria enquete nativa do WhatsApp |
| `!todos [msg]` | Menciona todos do grupo |
| `!link` | Link de convite do grupo |

---

## 🔧 Comandos Úteis

```bash
# Ver logs em tempo real
docker compose logs -f bot
docker compose logs -f celery-worker

# Reiniciar só o bot (sem rebuild)
docker compose restart bot

# Rebuild completo após mudanças no código
docker compose up -d --build

# Ver status dos containers
docker compose ps

# Acessar Redis CLI
docker exec -it boteco-redis redis-cli

# Ver fila do Celery
docker exec -it boteco-redis redis-cli -n 2 KEYS "*"
```

---

## 🏗️ Arquitetura

```
WhatsApp
   │
   ▼
Evolution API (Baileys)
   │  MESSAGES_UPSERT (webhook + base64=true)
   ▼
FastAPI /webhook
   │
   ├── DevGuard (valida, deduplica, extrai identidade)
   │
   ▼
handle_message.py
   │
   ├── guardrails.py (regex router)
   │
   ├─── Resposta imediata → Evolution API (sendText)
   │
   └─── Task pesada → Celery Worker
              │
              ├── task_dj: yt-dlp → mp3 → sendWhatsAppAudio
              └── task_figurinha: base64 → Pillow → webp → sendSticker
```

---

## 🚨 Solução de Problemas

**Bot não responde:**
```bash
docker compose logs bot --tail=50
# Verificar se o webhook está configurado e acessível externamente
```

**Músicas não tocam:**
```bash
docker compose logs celery-worker --tail=50
# Verificar se o yt-dlp está atualizado
docker exec boteco-worker yt-dlp --version
```

**Figurinhas via reply não funcionam (erro 400):**  
Adicione ao `docker-compose.yml` na Evolution API:
```yaml
- DATABASE_SAVE_DATA_NEW_MESSAGE=true
```
Fotos enviadas diretamente com `!s` continuam funcionando sem essa configuração.

**IA não responde:**  
Certifique-se de chamar com `!bot`, `!ai` ou `!boteco`. A IA não responde a mensagens sem comando.

---

## 📄 Licença

MIT — use, modifique e compartilhe à vontade. Se melhorar, manda um PR! 🍺