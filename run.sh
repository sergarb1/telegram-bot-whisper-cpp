#!/bin/bash
#USE THIS ONLY IF YOU RUN A STANDALONE INSTALLATION (DONT RUN FROM DOCKER)
export TELEGRAM_BOT_TOKEN=
# Optional (comma-separated list, leave empty to deny all)
export ALLOWED_CHAT_IDS=
export WHISPER_MODEL=tiny
export AUDIO_LANGUAGE=
python3 telegram_whisper_bot.py
