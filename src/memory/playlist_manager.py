"""
memory/playlist_manager.py — O Caderno do DJ 📓
================================================
Gere a fila de músicas usando as listas do Redis.
"""
import redis
from src.infrastructure.settings import settings

# Criamos uma conexão direta ao Redis (DB 1) configurado no settings
def _get_redis():
    # decode_responses=True já devolve strings em vez de bytes!
    return redis.from_url(settings.REDIS_URL, decode_responses=True)

def adicionar_a_fila(chat_id: str, nome_musica: str) -> int:
    """Adiciona uma música ao final da fila do grupo e retorna o tamanho da fila."""
    r = _get_redis()
    chave_fila = f"playlist:{chat_id}"
    return r.rpush(chave_fila, nome_musica)

def pegar_proxima_musica(chat_id: str) -> str | None:
    """Tira a primeira música da fila e retorna o nome dela."""
    r = _get_redis()
    chave_fila = f"playlist:{chat_id}"
    return r.lpop(chave_fila)

def ver_fila(chat_id: str) -> list[str]:
    """Retorna todas as músicas que estão na fila atualmente."""
    r = _get_redis()
    chave_fila = f"playlist:{chat_id}"
    return r.lrange(chave_fila, 0, -1)

def limpar_fila(chat_id: str):
    """Apaga a fila de músicas do grupo."""
    r = _get_redis()
    chave_fila = f"playlist:{chat_id}"
    r.delete(chave_fila)

def dj_esta_ocupado(chat_id: str) -> bool:
    """Verifica se o bot já está a baixar/enviar uma música para este grupo."""
    r = _get_redis()
    return bool(r.get(f"lock:dj:{chat_id}"))

def set_dj_ocupado(chat_id: str, ocupado: bool):
    """Tranca ou destranca o DJ para este grupo (com timeout de segurança de 5 min)."""
    r = _get_redis()
    chave = f"lock:dj:{chat_id}"
    if ocupado:
        r.setex(chave, 300, "1")
    else:
        r.delete(chave)