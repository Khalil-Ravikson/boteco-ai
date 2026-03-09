# 🍻 Boteco AI - O "Rythm" do WhatsApp

O **Boteco AI** é um bot de entretenimento e moderação para grupos de WhatsApp. Construído com uma arquitetura assíncrona robusta (FastAPI + Celery), ele permite baixar músicas do YouTube direto no chat, criar figurinhas instantâneas e interagir com a inteligência artificial do DeepSeek.

## 🚀 Funcionalidades

* 🎵 **DJ do Zap (`!play [música]`):** Busca no YouTube, baixa o áudio via `yt-dlp` e envia como áudio nativo usando filas em background (Celery).
* 🖼️ **Fábrica de Figurinhas (`!figurinha`):** Converte qualquer imagem enviada num sticker (webp) instantaneamente.
* 📣 **Megafone (`!todos [msg]`):** Marca todos os membros do grupo numa única mensagem.
* 🧠 **Chat com IA Livre:** Alimentado pelo **DeepSeek**, responde a perguntas de forma descontraída como um membro do grupo.
* ⚡ **Zero Travamentos:** O processamento pesado de vídeos é delegado aos workers do Celery, mantendo a API rápida e responsiva.

## 🛠️ Stack Tecnológica

* **Python 3.11+**
* **FastAPI** (Recebimento de Webhooks)
* **Celery + Redis** (Filas de tarefas para download de músicas)
* **Evolution API** (Motor de conexão com o WhatsApp)
* **DeepSeek API** (Cérebro do bot)
* **yt-dlp + FFmpeg** (Extração de áudio)

## 🐳 Como Rodar (Docker)

1. Clone o repositório:
   ```bash
   git clone [https://github.com/SEU_USUARIO/boteco-ai.git](https://github.com/SEU_USUARIO/boteco-ai.git)
   cd boteco-ai