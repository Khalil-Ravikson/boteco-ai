"""
application/handle_message.py — O Maestro do Boteco 🎼
=======================================================
CORREÇÃO: task_gerar_figurinha agora recebe (chat_id, media_base64)
em vez de (message_id, chat_id). O base64 vem do payload do webhook.
"""
import logging
from src.services.evolution_service import EvolutionService
from src.domain.guardrails import guardrails
from src.agent.core import agent_boteco
from src.memory.playlist_manager import adicionar_a_fila, ver_fila, limpar_fila, tentar_ocupar_dj
from src.application.tasks import task_dj_tocar_musica, task_gerar_figurinha

logger = logging.getLogger(__name__)


async def processar_mensagem(identity: dict, evolution: EvolutionService):
    chat_id      = identity["chat_id"]
    sender_phone = identity["sender_phone"]
    push_name    = identity["push_name"]
    body         = identity["body"]
    has_media    = identity["has_media"]
    media_base64 = identity.get("media_base64")  # ✅ base64 do webhook

    acao_bot = guardrails.analisar(body, has_media)

    # Bloco 1 — Resposta imediata
    if acao_bot.resposta_rapida:
        await evolution.enviar_mensagem(chat_id, acao_bot.resposta_rapida)

    # Bloco 2 — Ação principal
    if acao_bot.acao == "TOCAR_MUSICA":
        musica_pedida = acao_bot.parametro
        if tentar_ocupar_dj(chat_id):
            await evolution.enviar_mensagem(chat_id, f"🎵 Na mão! Buscando: *{musica_pedida}*...")
            task_dj_tocar_musica.delay(chat_id, musica_pedida)
        else:
            tamanho_fila = adicionar_a_fila(chat_id, musica_pedida)
            await evolution.enviar_mensagem(
                chat_id,
                f"📝 DJ ocupado! *{musica_pedida}* foi pra fila (Posição: {tamanho_fila})",
            )

    elif acao_bot.acao == "VER_FILA":
        fila = ver_fila(chat_id)
        if not fila:
            await evolution.enviar_mensagem(chat_id, "🪹 A fila tá vazia! Manda um `!play`.")
        else:
            texto_fila = "🎶 *FILA DA JUKEBOX* 🎶\n\n"
            for i, som in enumerate(fila, 1):
                texto_fila += f"{i}. {som}\n"
            await evolution.enviar_mensagem(chat_id, texto_fila)

    elif acao_bot.acao == "LIMPAR_FILA":
        limpar_fila(chat_id)

    elif acao_bot.acao == "FAZER_FIGURINHA":
        if not media_base64:
            # Segurança extra: não deveria chegar aqui sem base64
            await evolution.enviar_mensagem(
                chat_id,
                "⚠️ Não consegui obter a imagem. Tenta mandar a foto de novo com `!s`!",
            )
            return
        logger.info("🎨 Enviando task de figurinha para %s (base64=%d chars)", chat_id, len(media_base64))
        task_gerar_figurinha.delay(chat_id, media_base64)

    elif acao_bot.acao == "CHAMAR_TODOS":
        await evolution.enviar_mensagem(chat_id, acao_bot.parametro)

    elif acao_bot.acao == "LLM":
        corpo_com_nome = f"[{push_name}]: {body}"
        resposta_final = await agent_boteco.conversar(
            user_id=sender_phone,
            session_id=chat_id,
            mensagem=corpo_com_nome,
        )
        await evolution.enviar_mensagem(chat_id, resposta_final)