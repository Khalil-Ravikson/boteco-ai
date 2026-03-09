"""
application/handle_message.py — O Maestro do Boteco 🎼
=======================================================
Recebe a mensagem, passa pelo Regex e aciona a ação correta.
"""
import logging
from src.services.evolution_service import EvolutionService
from src.domain.guardrails import guardrails
from src.agent.core import agent_boteco  
# 👇 Aqui está o import corrigido! 👇
from src.memory.playlist_manager import adicionar_a_fila, ver_fila, limpar_fila, tentar_ocupar_dj
from src.application.tasks import task_dj_tocar_musica, task_gerar_figurinha

logger = logging.getLogger(__name__)

async def processar_mensagem(identity: dict, evolution: EvolutionService):
    chat_id = identity["chat_id"]
    sender_phone = identity["sender_phone"]
    body = identity["body"]
    has_media = identity["has_media"]
    message_id = identity["message_id"]
    # 🟢 CAPTURA O PUXÃO DE LADO (Reply)
    quoted_id = identity.get("quoted_message_id")
    quoted_type = identity.get("quoted_type") # ex: 'imageMessage'
    has_media = identity["has_media"] or (quoted_type == "imageMessage")
    # 1. Roteador Regex decide o que fazer
    acao_bot = guardrails.analisar(body, has_media)

    # 2. Respostas imediatas (Menu, Erros)
    if acao_bot.resposta_rapida:
        await evolution.enviar_mensagem(chat_id, acao_bot.resposta_rapida)

    # 3. Execução das Ações

    # 🎵 MÚSICA
    elif acao_bot.acao == "TOCAR_MUSICA":
        musica_pedida = acao_bot.parametro
        
        # O novo Lock Atómico em ação!
        if tentar_ocupar_dj(chat_id):
            await evolution.enviar_mensagem(chat_id, f"🎵 Na mão! Buscando: *{musica_pedida}*...")
            task_dj_tocar_musica.delay(chat_id, musica_pedida)
        else:
            # Se não conseguiu ocupar, o DJ já está tocando e adicionamos à fila
            tamanho_fila = adicionar_a_fila(chat_id, musica_pedida)
            await evolution.enviar_mensagem(chat_id, f"📝 DJ ocupado! *{musica_pedida}* foi pra fila (Posição: {tamanho_fila})")

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
        # O guardrails já envia a resposta de confirmação

    # 🖼️ FIGURINHA
    elif acao_bot.acao == "FAZER_FIGURINHA":
        # 🟢 Pega o ID da mensagem respondida (se houver)
        quoted_id = identity.get("quoted_message_id")
        quoted_type = identity.get("quoted_type")
        # Define se o alvo é a foto citada ou a foto atual
        target_id = quoted_id if (quoted_id and quoted_type == "imageMessage") else message_id
        logger.info(f"🎨 Enviando task de figurinha para o ID: {target_id}")
        task_gerar_figurinha.delay(target_id, chat_id)

    # 📣 CHAMAR TODOS
    elif acao_bot.acao == "CHAMAR_TODOS":
        texto = acao_bot.parametro or "📣 Acorda galera!"
        await evolution.enviar_mensagem(chat_id, texto)

    # 🧠 BATER PAPO (Com Memória!)
    elif acao_bot.acao == "LLM":
        # Formata a mensagem com o nome de quem enviou (Útil para grupos)
        corpo_com_nome = f"[{identity['push_name']}]: {body}"
        
        resposta_final = await agent_boteco.conversar(
            user_id=sender_phone, 
            session_id=chat_id,
            mensagem=corpo_com_nome
        )
        await evolution.enviar_mensagem(chat_id, resposta_final)