"""
main.py — O Ponto de Partida do Boteco 🚀
==========================================
Inicializa a API, Redis e conecta o Webhook.
"""
import logging
from fastapi import FastAPI
from src.infrastructure.settings import settings
from src.application.handle_webhook import router as webhook_router
from src.infrastructure.redis_client import inicializar_redis

# Configuração de Logs
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Boteco AI 🍻", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Abrindo as portas do Boteco AI...")
    
    # Inicia a conexão ao Redis
    inicializar_redis()
    
    logger.info("✅ Tudo pronto. À espera de clientes...")

# Rotas
app.include_router(webhook_router)

# Rota de health-check (Para saberes se o servidor está online)
@app.get("/")
def health_check():
    return {"status": "online", "boteco": "aberto"}