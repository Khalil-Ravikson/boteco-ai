"""
application/handle_message.py — O Maestro do Boteco 🎼
=======================================================
Recebe a mensagem, passa pelo Regex e aciona a ação correta.
"""
import logging
from src.services.evolution_service import EvolutionService
from src.domain.guardrails import guardrails
from src.providers.deepseek_provider import chamar_deepseek
from src.agent.validator import validar_deepseek
from src.memory.playlist_manager import adicionar_a_fila, ver_fila, limpar_fila, dj_esta_ocupado
from src.application.tasks import task_dj_tocar_musica, task_gerar_figurinha

logger = logging.getLogger(__name__)

async def processar_mensagem(identity: dict, evolution: EvolutionService):
    """
    Processa a mensagem validada pelo DevGuard.
    `identity` contém: chat_id, sender_phone, body, has_media, push_name, message_id
    """
    chat_id = identity["chat_id"]
    body = identity["body"]
    has_media = identity["has_media"]
    message_id = identity["message_id"]

    logger.info("📨 Analisando pedido: '%s'", body)

    # 1. O Roteador Regex decide o que fazer (0 tokens gastos)
    acao_bot = guardrails.analisar(body, has_media)

    # 2. Respostas imediatas síncronas (Ex: Menu, erros, confirmações de limpeza)
    if acao_bot.resposta_rapida:
        await evolution.enviar_mensagem(chat_id, acao_bot.resposta_rapida)

    # 3. Execução da Ação
    
    # 🎵 MÚSICA
    if acao_bot.acao == "TOCAR_MUSICA":
        musica_pedida = acao_bot.parametro
        
        if not dj_esta_ocupado(chat_id):
            # O DJ tá livre. Toca agora!
            await evolution.enviar_mensagem(chat_id, f"🎵 Opa meu nobre, tá na mão: *{musica_pedida}* (A baixar...)")
            task_dj_tocar_musica.delay(chat_id, musica_pedida)
        else:
            # O DJ tá ocupado. Vai para a fila!
            posicao = adicionar_a_fila(chat_id, musica_pedida)
            await evolution.enviar_mensagem(chat_id, f"📝 O DJ já tá tocando uma! *{musica_pedida}* foi pra fila (Posição: {posicao})")

    elif acao_bot.acao == "VER_FILA":
        fila = ver_fila(chat_id)
        if not fila:
            await evolution.enviar_mensagem(chat_id, "🪹 A fila tá mais vazia que meu copo! Manda um `!play`.")
        else:
            texto_fila = "🎶 *FILA DA JUKEBOX* 🎶\n\n"
            for i, som in enumerate(fila, 1):
                texto_fila += f"{i}. {som}\n"
            await evolution.enviar_mensagem(chat_id, texto_fila)

    elif acao_bot.acao == "LIMPAR_FILA":
        limpar_fila(chat_id)
        # A resposta já foi enviada no passo 2

    # 🖼️ FIGURINHA
    elif acao_bot.acao == "FAZER_FIGURINHA":
        # Aciona o Celery para não travar o bot enquanto a API converte
        task_gerar_figurinha.delay(message_id, chat_id)

    # 📣 CHAMAR TODOS
    elif acao_bot.acao == "CHAMAR_TODOS":
        texto = acao_bot.parametro or "📣 Acorda galera!"
        # Como o envio normal da Evolution API não marca todos nativamente sem a lista,
        # fazemos um truque com "group_mentions" (depende da doc oficial da sua versão)
        await evolution.enviar_mensagem(chat_id, texto) # TODO: Implementar menção fantasma

    # 🧠 BATER PAPO (DeepSeek)
    elif acao_bot.acao == "LLM":
        # Chama a IA
        resposta_bruta = await chamar_deepseek(body)
        
        # O Segurança limpa o papo corporativo
        resultado_validado = validar_deepseek(resposta_bruta)
        
        # Envia a resposta final para o grupo
        await evolution.enviar_mensagem(chat_id, resultado_validado.output)