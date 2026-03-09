"""
application/tasks.py — Os Trabalhadores do Boteco 👷‍♂️
======================================================
Tarefas assíncronas do Celery (DJ, Figurinhas, etc).
"""
import asyncio
import logging
from src.infrastructure.celery_app import celery_app
from src.services.evolution_service import EvolutionService

# Ferramentas e Memória
from src.tools.tool_dj import baixar_e_enviar_musica
from src.tools.tool_sticker import gerar_figurinha_via_api
from src.memory.playlist_manager import pegar_proxima_musica, set_dj_ocupado

logger = logging.getLogger(__name__)

# Instanciamos o serviço do WhatsApp para os workers usarem
evolution = EvolutionService()

@celery_app.task(name="tocar_playlist_grupo", bind=True)
def task_dj_tocar_musica(self, chat_id: str, primeira_musica: str = None):
    """
    O DJ do Boteco. Toca a música pedida e depois esvazia a fila do Redis.
    """
    # Se recebemos uma música direta, tocamos. Senão, puxamos a próxima da fila.
    musica_atual = primeira_musica or pegar_proxima_musica(chat_id)
    
    if not musica_atual:
        # Fila vazia! Destranca o DJ para ele poder descansar.
        logger.info("🪹 Fila vazia no chat %s. DJ descansando.", chat_id)
        set_dj_ocupado(chat_id, False)
        return

    # Tranca o DJ (timeout de 5 minutos gerido pelo Redis)
    set_dj_ocupado(chat_id, True)

    try:
        # Executa o download assíncrono (yt-dlp + ffmpeg)
        asyncio.run(baixar_e_enviar_musica(musica_atual, chat_id, evolution))
    except Exception as e:
        logger.error("❌ Erro no Celery ao tocar %s: %s", musica_atual, e)
    finally:
        # A MÁGICA: A task chama-se a si mesma com 3 segundos de atraso 
        # para puxar a próxima música da fila!
        task_dj_tocar_musica.apply_async(args=[chat_id, None], countdown=3)

@celery_app.task(name="gerar_figurinha_task")
def task_gerar_figurinha(message_id: str, chat_id: str):
    """Chama a API para converter a imagem em sticker."""
    asyncio.run(gerar_figurinha_via_api(message_id, chat_id))