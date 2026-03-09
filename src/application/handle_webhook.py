"""
application/handle_webhook.py — A Porta de Entrada 🔌
======================================================
Recebe os eventos do WhatsApp (Evolution API) e envia para processamento.
"""
import logging
from fastapi import APIRouter, Request, BackgroundTasks
from src.middleware.dev_guard import DevGuard
from src.infrastructure.redis_client import get_redis_text
from src.services.evolution_service import EvolutionService
from src.application.handle_message import processar_mensagem

logger = logging.getLogger(__name__)
router = APIRouter()
evolution_service = EvolutionService()

@router.post("/webhook")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        redis_conn = get_redis_text()
        guard = DevGuard(redis_conn)
        
        # O Segurança verifica se a mensagem é válida e do grupo correto
        valido, identity = await guard.validar(payload)
        
        if valido:
            # Lança o processamento em background (assim a API responde 200 OK na hora)
            background_tasks.add_task(processar_mensagem, identity, evolution_service)
            
        return {"status": "ok", "valido": valido}
        
    except Exception as e:
        logger.error(f"❌ Erro crítico no webhook: {e}")
        return {"status": "error", "message": str(e)}