"""
providers/groq_provider.py — O Motor Ultrarrápido do Boteco ⚡
============================================================
Usa AsyncOpenAI para falar com o Groq com estabilidade total.
"""
import logging
from openai import AsyncOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt
from src.infrastructure.settings import settings
from src.agent.prompts import SYSTEM_BOTECO

logger = logging.getLogger(__name__)

# O Groq é 100% compatível com a biblioteca da OpenAI
client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def chamar_groq(prompt_usuario: str, system_prompt: str = SYSTEM_BOTECO) -> str:
    """
    Chama a API do Groq de forma assíncrona e estável.
    """
    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL, # Ex: llama-3.3-70b-versatile
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=settings.GROQ_TEMP, 
            max_tokens=settings.GROQ_MAX_TOKENS
        )
        
        conteudo = response.choices[0].message.content
        logger.info("✅ Groq respondeu com sucesso.")
        return conteudo

    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg:
            logger.warning("⏳ Rate limit no Groq. O retry vai tentar novamente...")
            raise e # Lança para o tenacity fazer o retry
        
        logger.error(f"❌ Erro na API do Groq: {e}")
        return "O barman está ocupado a limpar o balcão. Tenta de novo num segundo! 🍺"