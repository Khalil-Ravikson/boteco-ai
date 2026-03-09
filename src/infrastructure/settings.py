"""
infrastructure/settings.py — Configurações do Boteco AI 🍻
============================================================
Usando Pydantic para validar variáveis de ambiente (.env).
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
    DEEPSEEK_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.7  # Mais alto para respostas descontraídas/engraçadas

    # ── Redis (Fila do Celery e Memória) ──────────────────────────────────────
    REDIS_URL: str = "redis://redis-stack:6379/1"
    CELERY_BROKER_URL: str = "redis://redis-stack:6379/0"

    # ── Evolution API (WhatsApp) ──────────────────────────────────────────────
    EVOLUTION_BASE_URL:      str = "http://evolution-api:8080"
    EVOLUTION_API_KEY:       str = ""
    EVOLUTION_INSTANCE_NAME: str = "default"
    WHATSAPP_HOOK_URL:       str = "http://boteco-ai:9000/webhook"

    # ── Comportamento do Agente & Memória ─────────────────────────────────────
    MAX_HISTORY_MESSAGES: int = 10    # Lembra das últimas 10 mensagens (poupa tokens)
    AGENT_TIMEOUT_S: int = 15         # Respostas rápidas para não perder o timing da piada
    AGENT_MAX_ITERATIONS: int = 3     # Previne loops infinitos e gastos desnecessários
    ROUTER_SIMILARITY_THRESHOLD: float = 0.45 

    # ── Segurança e Limites ───────────────────────────────────────────────────
    GRUPO_PERMITIDO: str = ""         # ID do grupo onde o bot pode atuar (ex: 123456@g.us)

    # ── Dev / Debug ───────────────────────────────────────────────────────────
    DEV_MODE:      bool = False
    DEV_WHITELIST: str  = ""          # Números permitidos no modo dev (separados por vírgula)
    LOG_LEVEL:     str  = "INFO"

    @property
    def dev_whitelist_list(self) -> list[str]:
        if not self.DEV_WHITELIST:
            return []
        return [n.strip() for n in self.DEV_WHITELIST.split(",") if n.strip()]

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()