"""
application/handle_message.py — O Maestro do Boteco 🎼
=======================================================
Recebe a mensagem, passa pelo Regex e aciona a ação correta.
"""
import logging
from src.services.evolution_service import EvolutionService
from src.domain.guardrails import guardrails
from src.agent.core import agent_boteco  # <-- O nosso novo cérebro com memória!
from src.memory.playlist_manager import adicionar_a_fila, ver_fila, limpar_fila, dj_esta_ocupado
from src.application.tasks import task_dj_tocar_musica, task_gerar_figurinha

logger = logging.getLogger(__name__)

async def processar_mensagem(identity: dict, evolution: EvolutionService):
    chat_id = identity["chat_id"]
    sender_phone = identity["sender_phone"]
    body = identity["body"]
    has_media = identity["has_media"]
    message_id = identity["message_id"]

    # 1. Roteador Regex decide o que fazer
    acao_bot = guardrails.analisar(body, has_media)

    # 2. Respostas imediatas (Menu, Erros)
    if acao_bot.resposta_rapida:
        await evolution.enviar_mensagem(chat_id, acao_bot.resposta_rapida)

    # 3. Execução das Ações

    # 🎵 MÚSICA
    if acao_bot.acao == "TOCAR_MUSICA":
        musica_pedida = acao_bot.parametro
        if not dj_esta_ocupado(chat_id):
            await evolution.enviar_mensagem(chat_id, f"🎵 Opa meu nobre, tá na mão: *{musica_pedida}* (A baixar...)")
            task_dj_tocar_musica.delay(chat_id, musica_pedida)
        else:
            posicao = adicionar_a_fila(chat_id, musica_pedida)
            await evolution.enviar_mensagem(chat_id, f"📝 O DJ já tá tocando uma! *{musica_pedida}* foi pra fila (Posição: {posicao})")

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

    # 🖼️ FIGURINHA
    elif acao_bot.acao == "FAZER_FIGURINHA":
        task_gerar_figurinha.delay(message_id, chat_id)

    # 📣 CHAMAR TODOS
    elif acao_bot.acao == "CHAMAR_TODOS":
        texto = acao_bot.parametro or "📣 Acorda galera!"
        await evolution.enviar_mensagem(chat_id, texto)

    # 🧠 BATER PAPO (Com Memória!)
    elif acao_bot.acao == "LLM":
        # Usamos o chat_id como session_id para o grupo inteiro partilhar a memória
        resposta_final = await agent_boteco.conversar(
            user_id=sender_phone, 
            session_id=chat_id,
            mensagem=body
        )
        await evolution.enviar_mensagem(chat_id, resposta_final)