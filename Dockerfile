FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y forzar salida de logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema (ffmpeg es vital para procesar media)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar (aprovechando la caché de capas de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de nuestra bestia
COPY telegram_whisper_bot.py .

# Crear usuario sin privilegios por seguridad y preparar carpeta temporal interna
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app/tmp && \
    chown -R botuser:botuser /app

# Cambiar al usuario seguro
USER botuser

# Variables de entorno por defecto
ENV TMP_PATH=/app/tmp
ENV WHISPER_MODEL=small
ENV AUDIO_LANGUAGE=""

# IMPORTANTE: Definir dónde guarda HuggingFace el modelo para poder cachearlo
ENV HF_HOME=/home/botuser/.cache/huggingface

# Arrancar el bot
CMD ["python", "telegram_whisper_bot.py"]