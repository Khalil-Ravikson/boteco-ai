"""
tools/tool_sticker.py — O Fazedor de Figurinhas 🖼️
===================================================
Pede à Evolution API para transformar uma imagem enviada num Sticker.
"""
import logging
import httpx
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)

async def gerar_figurinha_via_api(message_id: str, chat_id: str):
    """
    Pede à Evolution API para responder à mensagem original gerando um sticker.
    """
    url = f"{settings.EVOLUTION_BASE_URL}/message/sendWhatsAppSticker/{settings.EVOLUTION_INSTANCE_NAME}"
    headers = {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    
    # O truque da Evolution API: mandamos ela olhar para a mensagem original!
    payload = {
        "number": chat_id,
        "options": {
            "quoted": {"key": {"id": message_id}}, # Responde à imagem do utilizador
            "delay": 1000
        }
    }
    
    logger.info("🎨 Pedindo à Evolution API para gerar Sticker...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code in [200, 201]:
                logger.info("✅ Sticker gerado com sucesso!")
            else:
                logger.error("❌ Falha ao enviar sticker: %s", resp.text)
    except Exception as e:
        logger.error("❌ Erro na ferramenta de figurinha: %s", e)