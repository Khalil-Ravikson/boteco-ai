"""
middleware/dev_guard.py — O Segurança do Boteco 🛡️
===================================================
CORREÇÃO FINAL: O base64 da imagem vem em message.base64 (não dentro
de imageMessage). Formato confirmado nos logs da Evolution API v2.3.7.

Estrutura real do payload com Webhook Base64 ativo:
  message: {
    imageMessage: { url, mimetype, ... },  ← metadados
    messageContextInfo: { ... },
    base64: '/9j/4AAQ...'                  ← base64 aqui, direto em message
  }
"""
from __future__ import annotations
import uuid
import logging
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)

_EVENTOS_MENSAGEM = {"messages.upsert"}

_TIPOS_MIDIA_SEM_TEXTO = {
    "audioMessage", "stickerMessage", "reactionMessage",
    "protocolMessage", "pollCreationMessage",
}

def _normalizar_numero(jid: str) -> str:
    return jid.split("@")[0].replace("+", "").replace(" ", "").strip()

def _resolver_chat_id(key: dict, msg_data: dict) -> str | None:
    remote_jid = key.get("remoteJid", "")
    if "@s.whatsapp.net" in remote_jid or "@g.us" in remote_jid:
        return remote_jid
    if "@lid" in remote_jid:
        sender_pn = msg_data.get("senderPn", "")
        if sender_pn and "@s.whatsapp.net" in sender_pn:
            return sender_pn
        return None
    return None

def _extrair_base64_midia(message: dict) -> str | None:
    """
    Extrai base64 da imagem do payload.

    FORMATO CONFIRMADO (Evolution API v2.3.7 com Webhook Base64):
      message.base64  → string base64 da imagem original (campo direto em message)

    Também tenta message.imageMessage.jpegThumbnail como fallback
    caso o campo base64 não esteja presente (ex: reply de imagem).
    """
    # ✅ Campo principal — confirmado nos logs
    b64 = message.get("base64")
    if isinstance(b64, str) and len(b64) > 100:
        logger.debug("📎 base64 extraído de message.base64 (%d chars)", len(b64))
        return b64

    # Fallback: thumbnail dentro de imageMessage
    img_msg = message.get("imageMessage", {})
    if isinstance(img_msg, dict):
        thumbnail = img_msg.get("jpegThumbnail")
        if isinstance(thumbnail, str) and len(thumbnail) > 100:
            logger.debug("📎 base64 extraído de imageMessage.jpegThumbnail (%d chars)", len(thumbnail))
            return thumbnail

    # Fallback: imagem no quoted (reply com !s respondendo uma foto)
    context = message.get("contextInfo", {})
    if isinstance(context, dict):
        quoted = context.get("quotedMessage", {})
        if isinstance(quoted, dict):
            # base64 direto no quoted (se existir)
            b64_quoted = quoted.get("base64")
            if isinstance(b64_quoted, str) and len(b64_quoted) > 100:
                logger.debug("📎 base64 extraído de quotedMessage.base64 (%d chars)", len(b64_quoted))
                return b64_quoted
            # thumbnail do imageMessage quoted
            img_quoted = quoted.get("imageMessage", {})
            if isinstance(img_quoted, dict):
                thumbnail_q = img_quoted.get("jpegThumbnail")
                if isinstance(thumbnail_q, str) and len(thumbnail_q) > 100:
                    logger.debug("📎 base64 extraído de quotedMessage.imageMessage.jpegThumbnail")
                    return thumbnail_q

    logger.warning("⚠️  Nenhum base64 encontrado no payload da imagem")
    return None


class DevGuard:
    def __init__(self, redis_client):
        self.r = redis_client
        self.dev_mode = getattr(settings, "DEV_MODE", False)
        self.grupo_permitido = getattr(settings, "GRUPO_PERMITIDO", "").strip()
        self.allow_self = getattr(settings, "ALLOW_SELF_MESSAGES", False)

        whitelist_raw = getattr(settings, "DEV_WHITELIST", "")
        self.dev_whitelist = {
            _normalizar_numero(n)
            for n in whitelist_raw.split(",")
            if n.strip()
        } if isinstance(whitelist_raw, str) else set()

    async def validar(self, data: dict) -> tuple[bool, dict | str]:
        evento = data.get("event", "")
        if evento not in _EVENTOS_MENSAGEM:
            return False, "ignored_event"

        msg_data = data.get("data", {})
        if not msg_data or isinstance(msg_data, list):
            return False, "invalid_payload"

        key = msg_data.get("key", {})
        remote_jid = key.get("remoteJid", "")

        if key.get("fromMe", False) and not self.allow_self:
            return False, "ignored_self"

        if self.grupo_permitido and remote_jid != self.grupo_permitido:
            return False, "ignored_outside_official_group"

        if "broadcast" in remote_jid or "@newsletter" in remote_jid:
            return False, "ignored_broadcast"

        chat_id = _resolver_chat_id(key, msg_data)
        participant = key.get("participant") or remote_jid
        sender_phone = _normalizar_numero(participant)
        push_name = msg_data.get("pushName", "Visitante")

        if self.dev_mode and self.dev_whitelist:
            if sender_phone not in self.dev_whitelist:
                logger.info("🚧 DEV bloqueou %s no chat %s", sender_phone, chat_id)
                return False, "not_in_whitelist"

        message = msg_data.get("message", {})
        msg_type = msg_data.get("messageType", "unknown")

        context_info = message.get("contextInfo", {})
        quoted_msg = context_info.get("quotedMessage", {}) if isinstance(context_info, dict) else {}
        quoted_id = context_info.get("stanzaId") if isinstance(context_info, dict) else None
        quoted_type = list(quoted_msg.keys())[0] if quoted_msg else None

        body = (
            message.get("conversation")
            or message.get("extendedTextMessage", {}).get("text")
            or message.get("imageMessage", {}).get("caption")
            or ""
        ).strip()

        has_media = (
            "imageMessage" in message
            or quoted_type == "imageMessage"
        )

        # ✅ Extrai base64 usando o formato confirmado nos logs
        media_base64 = _extrair_base64_midia(message) if has_media else None

        if msg_type in _TIPOS_MIDIA_SEM_TEXTO and not body:
            return False, "ignored_media_no_text"

        event_id = key.get("id") or str(uuid.uuid4())
        if self.r:
            chave = f"evt:{event_id}"
            try:
                if self.r.get(chave):
                    return False, "duplicate"
                self.r.setex(chave, 300, "1")
            except Exception:
                pass

        identity = {
            "message_id":        key.get("id"),
            "chat_id":           chat_id,
            "sender_phone":      sender_phone,
            "push_name":         push_name,
            "body":              body,
            "has_media":         has_media,
            "msg_type":          msg_type,
            "quoted_message_id": quoted_id,
            "quoted_type":       quoted_type,
            "media_base64":      media_base64,
        }

        logger.info(
            "✅ Aprovada | chat=%s | user=%s | has_media=%s | media_b64=%s | cmd='%s'",
            chat_id, sender_phone, has_media,
            "sim" if media_base64 else "não",
            body[:30],
        )
        return True, identity