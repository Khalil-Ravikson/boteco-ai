"""
tools/tool_dj.py — O Baixador de Músicas 🎧
============================================
Usa yt-dlp para baixar áudio do YouTube e envia via Evolution API.
"""
import os
import uuid
import logging
import asyncio
from yt_dlp import YoutubeDL
from src.services.evolution_service import EvolutionService

logger = logging.getLogger(__name__)

async def baixar_e_enviar_musica(termo_busca: str, chat_id: str, evolution: EvolutionService):
    logger.info("🎧 Iniciando download da música: %s", termo_busca)
    
    file_id = str(uuid.uuid4())[:8]
    output_template = f"/tmp/{file_id}_%(title)s.%(ext)s"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'noplaylist': True,
        'default_search': 'ytsearch1:', # Pega o primeiro resultado da busca
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    arquivo_mp3 = None
    try:
        # Loop do evento (para não bloquear o worker do Celery)
        loop = asyncio.get_running_loop()
        
        def extrair_yt():
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{termo_busca}", download=True)
                if 'entries' in info:
                    info = info['entries'][0]
                arquivo_gerado = ydl.prepare_filename(info)
                return arquivo_gerado.rsplit('.', 1)[0] + '.mp3'

        # Roda o yt-dlp numa thread separada
        arquivo_mp3 = await loop.run_in_executor(None, extrair_yt)
        
        logger.info("✅ Download concluído: %s. Enviando para o WhatsApp...", arquivo_mp3)
        
        # Envia como áudio nativo do WhatsApp
        await evolution.enviar_audio_local(chat_id, arquivo_mp3)
        
    except Exception as e:
        logger.error("❌ Erro ao baixar música '%s': %s", termo_busca, e)
        await evolution.enviar_mensagem(chat_id, f"⚠️ Deu ruim a tentar baixar a música: {termo_busca}")
    finally:
        # Limpeza do arquivo temporário para não lotar o disco do servidor
        if arquivo_mp3 and os.path.exists(arquivo_mp3):
            os.remove(arquivo_mp3)
            logger.debug("🗑️ Arquivo temporário removido: %s", arquivo_mp3)