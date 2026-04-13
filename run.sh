#!/bin/bash

# =========================================================================
# USE THIS ONLY IF YOU RUN A STANDALONE INSTALLATION (DO NOT USE IN DOCKER)
# =========================================================================

# 1. Tu Token del Bot de Telegram (OBLIGATORIO)
export TELEGRAM_BOT_TOKEN="TU_TOKEN_AQUI"

# 2. IDs de los usuarios/grupos permitidos separados por comas (Opcional)
# Ejemplo: "123456789,-987654321" (Déjalo vacío para permitir a cualquiera)
export ALLOWED_CHAT_IDS=""

# 3. Modelo de Whisper (Opciones: tiny, base, small, medium, large-v3)
# 'small' es el punto dulce entre rapidez y precisión para una VPS normal.
export WHISPER_MODEL="small"

# 4. Idioma del audio (Opcional). 
# Déjalo vacío para que la IA lo detecte automáticamente, o pon "es" para forzar español.
export AUDIO_LANGUAGE=""

# 5. Carpeta temporal para descargar los audios y vídeos antes de procesarlos.
export TMP_PATH="/tmp"

# =========================================================================

# (Opcional) Si instalaste las librerías en un entorno virtual (venv), 
# quita la almohadilla (#) de la siguiente línea para activarlo automáticamente:
# source venv/bin/activate

echo "🚀 Arrancando Telegram Whisper Bot (God Mode) en modo Standalone..."
python3 telegram_whisper_bot.py