"""
test/test_boteco.py — Simulador Local do Boteco AI 🍻
======================================================
Testa a IA, a Memória Curta e os Comandos Regex diretamente no terminal,
sem precisar de ligar ao WhatsApp ou ao Celery.

COMO USAR:
1. Garante que o Redis local (ou Docker) está a correr.
2. Abre o terminal na raiz do projeto.
3. Roda: python -m test.test_boteco
"""
import asyncio
import logging
import sys
from pathlib import Path

# Garante que o projeto está no PYTHONPATH para encontrar os imports 'src.*'
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.redis_client import inicializar_redis
from src.domain.guardrails import guardrails
from src.agent.core import agent_boteco

# Desliga os logs muito verbosos para o terminal ficar limpo
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("src.providers").setLevel(logging.WARNING)
logging.getLogger("src.infrastructure").setLevel(logging.WARNING)

async def main():
    print("\n" + "="*50)
    print(" 🍻 SIMULADOR DO BOTECO AI 🍻")
    print("="*50)
    print("Escreve a tua mensagem e clica Enter.")
    print("Testa os comandos (!play, !menu, !figurinha) ou fala com a IA.")
    print("Escreve 'sair' para desligar o simulador.\n")

    # 1. Inicializa dependências (Apenas o Redis é necessário para a Memória)
    try:
        inicializar_redis()
    except Exception as e:
        print(f"❌ ERRO: O Redis não está ligado! ({e})")
        print("💡 Liga o teu Docker local do Redis primeiro: docker-compose up redis-stack -d")
        return

    # ID falso do grupo e do utilizador para simular
    fake_chat_id = "12345678@g.us"
    fake_user_id = "Mestre"

    while True:
        try:
            mensagem = input(f"\n👤 [{fake_user_id}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not mensagem:
            continue
        if mensagem.lower() in ["sair", "exit", "quit"]:
            print("👋 A fechar o Boteco! Fui!")
            break

        # 2. O Roteador Regex analisa a mensagem (Exatamente como o WhatsApp faz)
        acao_bot = guardrails.analisar(mensagem, has_media=False)

        # 3. Respostas Imediatas (Menu, Erros)
        if acao_bot.resposta_rapida:
            print(f"🤖 [Boteco]: {acao_bot.resposta_rapida}")
        
        # 4. Simulação das Ações Pesadas (Celery)
        if acao_bot.acao == "TOCAR_MUSICA":
            print(f"🎵 [Simulação Celery]: O DJ iria baixar '{acao_bot.parametro}' agora.")
        
        elif acao_bot.acao == "FAZER_FIGURINHA":
            print("🖼️ [Simulação Celery]: O worker iria fazer a figurinha (mas não mandaste imagem no terminal!)")
        
        elif acao_bot.acao == "VER_FILA":
            print("🪹 [Simulador Redis]: O Celery procuraria a fila no Redis agora.")
            
        elif acao_bot.acao == "CHAMAR_TODOS":
            print(f"📣 [Simulação Evolution]: Chamando toda a galera: {acao_bot.parametro}")

        # 5. O Cérebro (Bater papo com o DeepSeek e a Memória do Grupo)
        elif acao_bot.acao == "LLM":
            print("🧠 [DeepSeek a pensar...]")
            
            try:
                # O agent_boteco gere a memória no Redis local e chama a API do DeepSeek
                resposta_final = await agent_boteco.conversar(
                    user_id=fake_user_id,
                    session_id=fake_chat_id,
                    mensagem=mensagem
                )
                print(f"🤖 [Boteco]: {resposta_final}")
            except Exception as e:
                print(f"❌ Erro do Barman: {e}")

if __name__ == "__main__":
    asyncio.run(main())