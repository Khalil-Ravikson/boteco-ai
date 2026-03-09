"""
middleware/dev_guard.py — O Segurança do Boteco 🛡️ (Evolution API v2.3.7+)
=============================================================================
Filtra mensagens, restringe o bot ao grupo oficial e suporta REPLY (Puxão de lado).
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
    """'559887400509@s.whatsapp.net' → '559887400509'"""
    return jid.split("@")[0].replace("+", "").replace(" ", "").strip()

def _resolver_chat_id(key: dict, msg_data: dict) -> str | None:
    """Resolve o chat_id para enviar a resposta (Suporta fallback de @lid)."""
    remote_jid = key.get("remoteJid", "")

    if "@s.whatsapp.net" in remote_jid or "@g.us" in remote_jid:
        return remote_jid

    if "@lid" in remote_jid:
        sender_pn = msg_data.get("senderPn", "")
        if sender_pn and "@s.whatsapp.net" in sender_pn:
            return sender_pn
        return None

    return None

class DevGuard:
    def __init__(self, redis_client):
        self.r = redis_client
        self.dev_mode = getattr(settings, "DEV_MODE", False)
        self.grupo_permitido = getattr(settings, "GRUPO_PERMITIDO", "").strip()

        whitelist_raw = getattr(settings, "DEV_WHITELIST", "")
        self.dev_whitelist = {
            _normalizar_numero(n)
            for n in whitelist_raw.split(",")
            if n.strip()
        } if isinstance(whitelist_raw, str) else set()

    async def validar(self, data: dict) -> tuple[bool, dict | str]:
        """Valida, filtra e extrai a identidade completa da mensagem."""
        
        # 1. Filtro de evento básico
        evento = data.get("event", "")
        if evento not in _EVENTOS_MENSAGEM:
            return False, "ignored_event"

        msg_data = data.get("data", {})
        if not msg_data or isinstance(msg_data, list):
            return False, "invalid_payload"

        key = msg_data.get("key", {})
        remote_jid = key.get("remoteJid", "")

        # 2. Ignora mensagens enviadas pelo próprio bot
        if key.get("fromMe", False):
            return False, "ignored_self"

        # 3. 🔒 TRAVA DE SEGURANÇA: Bloqueia Privado e outros Grupos
        # Se um grupo oficial está definido, nada de fora entra.
        if self.grupo_permitido and remote_jid != self.grupo_permitido:
            # Silencioso para não encher o log, mas bloqueia.
            return False, "ignored_outside_official_group"

        # 4. Filtro de Broadcast/Newsletter
        if "broadcast" in remote_jid or "@newsletter" in remote_jid:
            return False, "ignored_broadcast"

        # 5. Resolve IDs e Sender
        chat_id = _resolver_chat_id(key, msg_data)
        participant = key.get("participant") or remote_jid
        sender_phone = _normalizar_numero(participant)
        push_name = msg_data.get("pushName", "Visitante")

        # 6. DEV_MODE: Bloqueio por Whitelist
        if self.dev_mode and self.dev_whitelist:
            if sender_phone not in self.dev_whitelist:
                logger.info("🚧 DEV bloqueou %s no chat %s", sender_phone, chat_id)
                return False, "not_in_whitelist"

        # 7. EXTRAÇÃO DE CONTEÚDO E REPLY (Puxão de lado)
        message = msg_data.get("message", {})
        msg_type = msg_data.get("messageType", "unknown")
        
        # Pega informações da mensagem respondida (quoted)
        context_info = message.get("contextInfo", {})
        quoted_msg = context_info.get("quotedMessage", {})
        quoted_id = context_info.get("stanzaId")
        quoted_type = list(quoted_msg.keys())[0] if quoted_msg else None

        # Tenta extrair o texto de qualquer lugar (Legenda, Texto normal, etc)
        body = (
            message.get("conversation")
            or message.get("extendedTextMessage", {}).get("text")
            or message.get("imageMessage", {}).get("caption")
            or ""
        ).strip()

        # 8. Filtro de Mídia sem comando
        if msg_type in _TIPOS_MIDIA_SEM_TEXTO and not body:
            return False, "ignored_media_no_text"

        # 9. Deduplicação via Redis (Evita o bot responder 2x a mesma msg)
        event_id = key.get("id") or str(uuid.uuid4())
        if self.r:
            chave = f"evt:{event_id}"
            try:
                if self.r.get(chave): return False, "duplicate"
                self.r.setex(chave, 300, "1")
            except: pass

        # 10. IDENTIDADE COMPLETA APROVADA
        identity = {
            "message_id":        key.get("id"),
            "chat_id":           chat_id,
            "sender_phone":      sender_phone,
            "push_name":         push_name,
            "body":              body,
            "has_media":         "imageMessage" in message,
            "msg_type":          msg_type,
            # 🟢 Campos vitais para figurinhas por reply:
            "quoted_message_id": quoted_id,
            "quoted_type":       quoted_type
        }

        logger.info("✅ Aprovada | chat=%s | user=%s | cmd='%s'", chat_id, sender_phone, body[:30])
        return True, identity