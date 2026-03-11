"""
application/tasks.py — v4 (base64 direto do webhook)
=====================================================
CORREÇÃO: task_gerar_figurinha agora recebe o base64 da imagem
diretamente, sem precisar chamar nenhum endpoint da Evolution API.
"""
import asyncio
import logging
from src.infrastructure.celery_app import celery_app
from src.services.evolution_service import EvolutionService
from src.tools.tool_dj import baixar_e_enviar_musica
from src.tools.tool_sticker import gerar_figurinha_via_api
from src.memory.playlist_manager import pegar_proxima_musica, liberar_dj

logger = logging.getLogger(__name__)

def get_evolution():
    return EvolutionService()


# ─── TAREFA 1: O DJ ────────────────────────────────────────────────────────
@celery_app.task(name="tocar_playlist_grupo", bind=True)
def task_dj_tocar_musica(self, chat_id: str, primeira_musica: str = None):
    musica_atual = primeira_musica or pegar_proxima_musica(chat_id)
    if not musica_atual:
        logger.info("🪹 Fila vazia em %s. DJ liberado.", chat_id)
        liberar_dj(chat_id)
        return
    try:
        evolution = get_evolution()
        asyncio.run(baixar_e_enviar_musica(musica_atual, chat_id, evolution))
    except Exception as e:
        logger.error("❌ Falha na task do DJ: %s", e)

    proxima = pegar_proxima_musica(chat_id)
    if proxima:
        task_dj_tocar_musica.apply_async(args=[chat_id, proxima], countdown=3)
    else:
        liberar_dj(chat_id)


# ─── TAREFA 2: O FAZEDOR DE FIGURINHAS ─────────────────────────────────────
@celery_app.task(name="gerar_figurinha_task")
def task_gerar_figurinha(chat_id: str, media_base64: str):
    """
    ✅ NOVO: recebe o base64 da imagem direto do webhook.
    Não precisa mais chamar nenhum endpoint da Evolution para buscar a mídia.
    """
    try:
        asyncio.run(gerar_figurinha_via_api(chat_id=chat_id, media_base64=media_base64))
    except Exception as e:
        logger.error("❌ Erro na task de figurinha: %s", e)