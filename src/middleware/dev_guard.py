"""
middleware/dev_guard.py — O Segurança do Boteco 🛡️ (Evolution API v2.3.7+)
=============================================================================
Filtra mensagens, restringe o bot ao grupo oficial e suporta DEV_MODE.
"""
from __future__ import annotations
import json
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
    """'559887400509@s.whatsapp.net' → '559887400509'"""
    return jid.split("@")[0].replace("+", "").replace(" ", "").strip()

def _resolver_chat_id(key: dict, msg_data: dict) -> str | None:
    """Resolve o chat_id para enviar a resposta (Suporta o fallback de @lid)."""
    remote_jid = key.get("remoteJid", "")

    if "@s.whatsapp.net" in remote_jid or "@g.us" in remote_jid:
        return remote_jid

    if "@lid" in remote_jid:
        sender_pn = msg_data.get("senderPn", "")
        if sender_pn and "@s.whatsapp.net" in sender_pn:
            logger.info("📱 @lid resolvido via senderPn: %s → %s", remote_jid, sender_pn)
            return sender_pn
        return None

    return None

class DevGuard:
    def __init__(self, redis_client):
        self.r = redis_client
        self.dev_mode = getattr(settings, "DEV_MODE", False)
        self.grupo_permitido = getattr(settings, "GRUPO_PERMITIDO", "").strip()

        whitelist_raw = getattr(settings, "DEV_WHITELIST", "")
        if isinstance(whitelist_raw, str):
            self.dev_whitelist = {
                _normalizar_numero(n)
                for n in whitelist_raw.split(",")
                if n.strip()
            }
        else:
            self.dev_whitelist = {_normalizar_numero(n) for n in whitelist_raw}

        # Logs de inicialização
        if self.grupo_permitido:
            logger.info("🛡️  Boteco exclusivo: Apenas o grupo %s pode entrar.", self.grupo_permitido)
        else:
            logger.info("🛡️  Boteco aberto: O bot vai responder em qualquer chat.")

        if self.dev_mode:
            logger.info("🚧 DEV_MODE=True | Apenas a whitelist pode falar com o bot: %s", self.dev_whitelist)

    async def validar(self, data: dict) -> tuple[bool, dict | str]:
        """Valida e filtra payload da Evolution API."""
        
        # 1. Filtro de evento e bloco data
        evento = data.get("event", "")
        if evento not in _EVENTOS_MENSAGEM:
            return False, "ignored_event"

        msg_data = data.get("data", {})
        if isinstance(msg_data, list) or not msg_data:
            return False, "invalid_payload"

        key = msg_data.get("key", {})
        remote_jid = key.get("remoteJid", "")

        # 2. Ignora mensagens próprias
        if key.get("fromMe", False):
            return False, "ignored_self"

        # 3. Filtros de origem (Grupo Permitido e Broadcast)
        if "broadcast" in remote_jid or "@newsletter" in remote_jid:
            return False, "ignored_broadcast"

        is_group = "@g.us" in remote_jid
        if is_group and self.grupo_permitido and remote_jid != self.grupo_permitido:
            logger.debug("⏭️  Grupo ignorado (não é o oficial): %s", remote_jid)
            return False, "ignored_wrong_group"

        # 4. Resolve chat_id e descobre quem enviou (Participant)
        chat_id = _resolver_chat_id(key, msg_data)
        if chat_id is None:
            return False, "unresolvable_id"

        # Num grupo, quem enviou está no 'participant'. No privado, é o próprio 'remoteJid'.
        participant = key.get("participant") or remote_jid
        sender_phone = _normalizar_numero(participant)
        push_name = msg_data.get("pushName", "")

        # 5. DEV_MODE: whitelist (Agora funciona mesmo dentro do grupo!)
        if self.dev_mode and self.dev_whitelist:
            if sender_phone not in self.dev_whitelist:
                logger.info("🚧 DEV bloqueou %s ('%s') no chat %s", sender_phone, push_name, chat_id)
                return False, "not_in_whitelist"

        # 6. Extrai corpo da mensagem
        message = msg_data.get("message", {})
        msg_type = msg_data.get("messageType", "unknown")
        body = (
            message.get("conversation")
            or message.get("extendedTextMessage", {}).get("text")
            or message.get("imageMessage", {}).get("caption")
            or message.get("videoMessage", {}).get("caption")
            or message.get("documentMessage", {}).get("caption")
            or ""
        ).strip()

        # 7. Ignora mídia sem texto (Exceção: imagens para figurinhas terão legenda '!figurinha')
        if msg_type in _TIPOS_MIDIA_SEM_TEXTO and not body:
            return False, "ignored_media_no_text"

        # 8. Deduplicação via Redis
        event_id = key.get("id") or data.get("id") or str(uuid.uuid4())
        if self.r:
            chave = f"evt:{event_id}"
            try:
                if self.r.get(chave):
                    return False, "duplicate"
                self.r.setex(chave, 300, "1")
            except: pass

        # 9. Aprovado - Monta a identidade
        has_media = msg_type in {"imageMessage", "videoMessage"}

        identity = {
            "chat_id":      chat_id,       # Para onde o bot vai responder (Pode ser o grupo)
            "sender_phone": sender_phone,  # Quem realmente mandou a mensagem
            "body":         body,
            "has_media":    has_media,
            "msg_type":     msg_type,
            "push_name":    push_name,
            "message_id":   key.get("id", "") # CRÍTICO: Necessário para gerar figurinhas!
        }

        logger.info(
            "✅ Aprovada | chat=%s | user=%s | tipo=%s | '%s'",
            chat_id, sender_phone, msg_type, body[:60]
        )
        return True, identity