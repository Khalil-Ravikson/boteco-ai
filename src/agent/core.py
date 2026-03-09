"""
agent/core.py — O Cérebro do Boteco (Com Memória) 🧠
=========================================================
Substitui a pipeline RAG pesada. Gere a memória curta (Redis) e fala com a IA.
"""
import logging
import time
from src.providers.groq_provider import chamar_groq
from src.agent.validator import validar_resposta_ia
from src.memory.working_memory import adicionar_mensagem, get_historico_compactado
from src.agent.prompts import SYSTEM_BOTECO

logger = logging.getLogger(__name__)

class AgentBoteco:
    def __init__(self):
        self._inicializado = True
        logger.info("✅ AgentBoteco inicializado (Memória de Curto Prazo ATIVA).")

    async def conversar(self, user_id: str, session_id: str, mensagem: str) -> str:
        """
        Gere a conversa com memória curta e devolve a resposta final limpa.
        """
        t0 = time.monotonic()

        # 1. Recupera o histórico das últimas mensagens do Redis (Memória Curta)
        historico = get_historico_compactado(session_id)
        
        # 2. Formata o histórico e anexa ao Prompt de Sistema
        system_prompt_com_memoria = SYSTEM_BOTECO
        if historico and historico.texto_formatado:
            system_prompt_com_memoria += (
                f"\n\n[HISTÓRICO RECENTE DA CONVERSA NESTE GRUPO]\n"
                f"Use isso para dar contexto, mas responda apenas à última mensagem.\n"
                f"{historico.texto_formatado}"
            )

        # 3. Chama o DeepSeek (passando a personalidade + memória)
        resposta_bruta = await chamar_groq(
            prompt_usuario=mensagem, 
            system_prompt=system_prompt_com_memoria
        )

        # 4. O Segurança (Validator) limpa o papo corporativo da IA
        resultado_validado = validar_resposta_ia(resposta_bruta)
        resposta_final = resultado_validado.output

        # 5. Salva a nova interação na Memória (Redis) para o bot lembrar no futuro
        msg_formatada_user = f"[{user_id} disse]: {mensagem}"
        adicionar_mensagem(session_id, "user", msg_formatada_user)
        adicionar_mensagem(session_id, "assistant", resposta_final)

        latencia_ms = int((time.monotonic() - t0) * 1000)
        logger.info(f"📤 Resposta gerada | latência={latencia_ms}ms")

        return resposta_final

# Singleton global (É esta instância que o handle_message.py vai importar!)
agent_boteco = AgentBoteco()