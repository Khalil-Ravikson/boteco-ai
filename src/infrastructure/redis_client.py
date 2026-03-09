"""
infrastructure/redis_client.py — O Cérebro de Memória do Boteco 🍻
===================================================================
Fornece clientes Redis simples e limpos para guardar as conversas 
e gerir a fila do DJ, sem os índices pesados do RediSearch.
"""
from __future__ import annotations

import logging
from functools import lru_cache
import redis
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_redis_text() -> redis.Redis:
    """
    Cliente Redis principal do Boteco.
    Usado para: Histórico de chat e DevGuard.
    decode_responses=True garante que tudo o que entra/sai são Strings normais.
    """
    client = redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=10,
        retry_on_timeout=True,
        max_connections=20,
    )
    return client

def redis_ok() -> bool:
    """Verifica saúde do Redis. Usado no /health endpoint."""
    try:
        get_redis_text().ping()
        return True
    except Exception as e:
        logger.error("❌ Redis offline: %s", e)
        return False