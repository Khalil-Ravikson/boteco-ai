"""
application/tasks.py — v3 (DJ Estável + Figurinhas) 👷‍♂️
========================================================
Tarefas assíncronas do Celery.
"""
import asyncio
import logging
from src.infrastructure.celery_app import celery_app
from src.services.evolution_service import EvolutionService

# Ferramentas e Memória
from src.tools.tool_dj import baixar_e_enviar_musica
from src.tools.tool_sticker import gerar_figurinha_via_api
from src.memory.playlist_manager import pegar_proxima_musica, liberar_dj, tentar_ocupar_dj

logger = logging.getLogger(__name__)

# Factory para evitar EvolutionService global instanciado no import
def get_evolution():
    return EvolutionService()

# ─── TAREFA 1: O DJ ────────────────────────────────────────────────────────
@celery_app.task(name="tocar_playlist_grupo", bind=True)
def task_dj_tocar_musica(self, chat_id: str, primeira_musica: str = None):
    # 1. Decide o que tocar
    musica_atual = primeira_musica or pegar_proxima_musica(chat_id)
    
    # 2. Se não tem música, liberta o DJ e encerra
    if not musica_atual:
        logger.info("🪹 Fila vazia em %s. DJ liberado.", chat_id)
        liberar_dj(chat_id)
        return

    # 3. Execução do download/envio
    try:
        evolution = get_evolution()
        asyncio.run(baixar_e_enviar_musica(musica_atual, chat_id, evolution))
    except Exception as e:
        logger.error("❌ Falha na task do DJ: %s", e)
    
    # 4. Verifica se há mais na fila para continuar o loop
    proxima = pegar_proxima_musica(chat_id)
    if proxima:
        # Relança para a próxima música com um pequeno intervalo
        task_dj_tocar_musica.apply_async(args=[chat_id, proxima], countdown=3)
    else:
        # Fila acabou, liberta o DJ
        liberar_dj(chat_id)

# ─── TAREFA 2: O FAZEDOR DE FIGURINHAS ─────────────────────────────────────
@celery_app.task(name="gerar_figurinha_task")
def task_gerar_figurinha(message_id: str, chat_id: str):
    """Chama a API para converter a imagem em sticker."""
    try:
        evolution = get_evolution()
        # Passamos o evolution para o tool_sticker conseguir baixar a imagem
        asyncio.run(gerar_figurinha_via_api(message_id, chat_id, evolution))
    except Exception as e:
        logger.error("❌ Erro na task de figurinha: %s", e)