"""
memory/playlist_manager.py — v2 (Reforçado) 📓
"""
import redis
import logging
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)

# Singleton para o Pool de Conexões
_redis_pool = None

def _get_redis():
    global _redis_pool
    if _redis_pool is None:
        # Usamos o pool para gerir conexões de forma eficiente
        _redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL, 
            decode_responses=True,
            max_connections=20
        )
    return redis.Redis(connection_pool=_redis_pool)

def adicionar_a_fila(chat_id: str, nome_musica: str) -> int:
    r = _get_redis()
    return r.rpush(f"playlist:{chat_id}", nome_musica)

def pegar_proxima_musica(chat_id: str) -> str | None:
    r = _get_redis()
    return r.lpop(f"playlist:{chat_id}")

def ver_fila(chat_id: str) -> list[str]:
    r = _get_redis()
    return r.lrange(f"playlist:{chat_id}", 0, -1)

def limpar_fila(chat_id: str):
    r = _get_redis()
    r.delete(f"playlist:{chat_id}")
    r.delete(f"lock:dj:{chat_id}")

def tentar_ocupar_dj(chat_id: str) -> bool:
    """
    Tenta obter o lock atómico (SET NX). 
    Retorna True se conseguiu trancar, False se já estava ocupado.
    """
    r = _get_redis()
    # NX=True (Só cria se não existir), EX=300 (Expira em 5 min se o bot cair)
    return bool(r.set(f"lock:dj:{chat_id}", "1", nx=True, ex=300))

def liberar_dj(chat_id: str):
    r = _get_redis()
    r.delete(f"lock:dj:{chat_id}")