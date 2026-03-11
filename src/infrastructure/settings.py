"""
infrastructure/settings.py — Configurações do Boteco AI 🍻
============================================================
CORREÇÕES:
  - NOVO: ALLOW_SELF_MESSAGES — quando True, o dono do número conectado
    pode usar comandos (!play, !s, etc.) enviando mensagens para o grupo.
    Por padrão False (comportamento seguro original).
    Para ativar: adicione ALLOW_SELF_MESSAGES=true no .env
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE_PATH", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Inteligência Artificial (O Barman) ────────────────────────────────────
    DEEPSEEK_API_KEY: str   = ""
    LLM_TEMPERATURE:  float = 0.7

    GROQ_API_KEY:    str   = ""
    GROQ_MODEL:      str   = "llama-3.3-70b-versatile"
    GROQ_TEMP:       float = 0.7
    GROQ_MAX_TOKENS: int   = 300

    # ── Redis (Fila do Celery e Memória) ──────────────────────────────────────
    REDIS_URL:         str = "redis://boteco-redis:6379/1"
    CELERY_BROKER_URL: str = "redis://boteco-redis:6379/2"

    # ── Evolution API (WhatsApp) ──────────────────────────────────────────────
    EVOLUTION_BASE_URL:      str = "http://evolution-api:8080"
    EVOLUTION_API_KEY:       str = ""
    EVOLUTION_INSTANCE_NAME: str = "default"
    WHATSAPP_HOOK_URL:       str = "http://boteco-ai:9000/webhook"

    # ── Comportamento do Agente & Memória ─────────────────────────────────────
    MAX_HISTORY_MESSAGES:       int   = 10
    AGENT_TIMEOUT_S:            int   = 15
    AGENT_MAX_ITERATIONS:       int   = 3
    ROUTER_SIMILARITY_THRESHOLD: float = 0.45

    # ── Segurança e Limites ───────────────────────────────────────────────────
    GRUPO_PERMITIDO: str = ""

    # ── Dev / Debug ───────────────────────────────────────────────────────────
    DEV_MODE:      bool = False
    DEV_WHITELIST: str  = ""
    LOG_LEVEL:     str  = "INFO"

    # ✅ NOVO: permite que o dono do número use comandos no grupo
    #    Adicione ALLOW_SELF_MESSAGES=true no .env para ativar
    ALLOW_SELF_MESSAGES: bool = False

    @property
    def dev_whitelist_list(self) -> list[str]:
        if not self.DEV_WHITELIST:
            return []
        return [n.strip() for n in self.DEV_WHITELIST.split(",") if n.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()