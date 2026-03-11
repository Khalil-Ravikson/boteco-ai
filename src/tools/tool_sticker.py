"""
tools/tool_sticker.py — O Fazedor de Figurinhas 🖼️
===================================================
NOVO FLUXO (sem chamadas à Evolution API):
  1. Recebe o base64 da imagem diretamente do webhook (Webhook Base64 ativo)
  2. Converte para .webp 512x512 com Pillow
  3. Envia via /message/sendSticker

DEPENDÊNCIA: Pillow>=10.0.0 no requirements.txt
"""
import base64
import logging
from io import BytesIO

import httpx
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)

_STICKER_SIZE = (512, 512)


async def gerar_figurinha_via_api(chat_id: str, media_base64: str):
    """
    Converte base64 da imagem para .webp e envia como sticker.
    Não faz nenhuma chamada para buscar mídia — tudo vem do webhook.
    """
    if not media_base64:
        logger.error("❌ base64 da imagem não fornecido")
        return

    # Converte para .webp
    webp_b64 = _converter_para_webp(media_base64)
    if not webp_b64:
        return

    # Envia como sticker
    base_url = settings.EVOLUTION_BASE_URL.rstrip("/")
    instance = settings.EVOLUTION_INSTANCE_NAME
    headers = {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }

    logger.info("📤 Enviando sticker para %s...", chat_id)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{base_url}/message/sendSticker/{instance}",
                json={"number": chat_id, "sticker": webp_b64, "delay": 500},
                headers=headers,
            )
        if resp.status_code in (200, 201):
            logger.info("✅ Sticker enviado com sucesso para %s!", chat_id)
        else:
            logger.error(
                "❌ Falha ao enviar sticker: status=%s | %s",
                resp.status_code, resp.text[:300],
            )
    except Exception as e:
        logger.error("❌ Erro ao enviar sticker: %s", e)


def _converter_para_webp(imagem_b64: str) -> str | None:
    try:
        from PIL import Image

        # Remove prefixo data:image/xxx;base64, se existir
        if "," in imagem_b64:
            imagem_b64 = imagem_b64.split(",", 1)[1]

        img = Image.open(BytesIO(base64.b64decode(imagem_b64))).convert("RGBA")
        img.thumbnail(_STICKER_SIZE, Image.LANCZOS)

        canvas = Image.new("RGBA", _STICKER_SIZE, (0, 0, 0, 0))
        offset = (
            (_STICKER_SIZE[0] - img.width) // 2,
            (_STICKER_SIZE[1] - img.height) // 2,
        )
        canvas.paste(img, offset, mask=img)

        buffer = BytesIO()
        canvas.save(buffer, format="WEBP", quality=90)
        buffer.seek(0)

        logger.info("✅ Imagem convertida para .webp")
        return base64.b64encode(buffer.read()).decode("utf-8")

    except ImportError:
        logger.error(
            "❌ Pillow não instalado! "
            "Adicione Pillow>=10.0.0 ao requirements.txt e rode: "
            "docker compose build bot celery-worker && docker compose up -d"
        )
        return None
    except Exception as e:
        logger.error("❌ Erro ao converter imagem para .webp: %s", e)
        return None