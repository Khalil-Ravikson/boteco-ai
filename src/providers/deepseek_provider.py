"""
providers/deepseek_provider.py — O Barman do Boteco 🍻
======================================================
Integração assíncrona com o DeepSeek usando a biblioteca da OpenAI.
"""
import logging
from openai import AsyncOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt
from src.infrastructure.settings import settings
from src.agent.prompts import SYSTEM_BOTECO  # Importamos o prompt turbinado daqui!

logger = logging.getLogger(__name__)

# O truque: Usamos a biblioteca da OpenAI, mas apontamos para os servidores do DeepSeek
client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def chamar_deepseek(prompt_usuario: str, system_prompt: str = SYSTEM_BOTECO) -> str:
    """
    Chama a API do DeepSeek de forma assíncrona.
    """
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",  # Modelo rápido e barato
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=settings.LLM_TEMPERATURE, 
            max_tokens=300 # Garante respostas curtas
        )
        conteudo = response.choices[0].message.content
        logger.info("✅ DeepSeek respondeu com sucesso.")
        return conteudo
    except Exception as e:
        logger.error(f"❌ Erro na API do DeepSeek: {e}")
        return "Ih, deu azar no barril de chopp! 🍺 Tenta de novo em 1 minuto."