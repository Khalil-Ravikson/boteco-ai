# Dockerfile — Boteco AI 🍻
FROM python:3.11-slim

# Instala o FFmpeg (Obrigatório para o yt-dlp) e o curl (Para o healthcheck)
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do Boteco
COPY . .

EXPOSE 9000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "9000"]