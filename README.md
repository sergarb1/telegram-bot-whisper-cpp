# 🤖 Telegram Bot Transcriptor (con Faster-Whisper)

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Faster-Whisper](https://img.shields.io/badge/Faster--Whisper-Powered-FF6B6B.svg)

Un bot de Telegram extremadamente optimizado que transcribe notas de voz, vídeos y archivos de audio a texto usando **faster-whisper** (CTranslate2). Totalmente auto-alojado, privado y diseñado para exprimir al máximo servidores VPS con recursos limitados.

## ✨ Características

- 🎤 **Motor Ultrarrápido:** Migrado a `faster-whisper` con cuantización INT8, hasta 4 veces más rápido que Whisper original.
- 🔇 **Filtro VAD Inteligente:** Elimina silencios y ruidos de fondo *antes* de procesar, ahorrando hasta un 30% de CPU.
- ⏱️ **Cronómetro en vivo:** Edita su propio mensaje cada 15s para mostrarte el tiempo de procesamiento en directo.
- ✂️ **Divisor Automático de Textos:** Soporta audios largos (hasta 1 hora). Si el texto supera el límite de Telegram (4096 caracteres), lo envía ordenadamente en fragmentos como `[Parte 1/3]`.
- 🧹 **Gestión Extrema de RAM:** Fuerza la recolección de basura (Garbage Collection) tras cada transcripción para evitar cuelgues en servidores pequeños.
- 🎬 **Soporte Multimedia:** Acepta Notas de Voz, Audios MP3/WAV, Vídeos MP4 y Documentos.
- 🐳 **Docker Optimizado:** Incluye volumen de caché para que los modelos no se descarguen cada vez que reinicias.

## 🚀 Instalación Rápida (Recomendado: Docker)

# 1. Clona el repositorio
git clone [https://github.com/tuusuario/telegram-whisper-bot.git](https://github.com/tuusuario/telegram-whisper-bot.git)
cd telegram-whisper-bot

# 2. Configura las variables de entorno
cp .env.example .env
nano .env  # Añade el Token de tu bot y tu ID de Telegram

# 3. Construye e inicia el bot
docker-compose up -d --build

# 4. Verifica que está funcionando
docker-compose logs -f

## 💻 Instalación Manual (Standalone)

Si no quieres usar Docker, asegúrate de tener **FFmpeg** instalado en tu sistema (`sudo apt install ffmpeg`).

# 1. Clona el repositorio
git clone [https://github.com/tuusuario/telegram-whisper-bot.git](https://github.com/tuusuario/telegram-whisper-bot.git)
cd telegram-whisper-bot

# 2. Instala las dependencias de Python
pip install -r requirements.txt

# 3. Configura el script de arranque
nano run.sh # Añade tu TELEGRAM_BOT_TOKEN aquí

# 4. Da permisos y ejecuta
chmod +x run.sh
./run.sh

## 🔧 Configuración (`.env`)

Crea un archivo `.env` en la raíz del proyecto. Tienes una plantilla en `.env.example`.

# [REQUERIDO] Token proporcionado por @BotFather
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# [OPCIONAL] IDs de usuarios permitidos (separados por comas). Vacío = Público.
ALLOWED_CHAT_IDS=123456789,987654321

# Configuración de Whisper
WHISPER_MODEL=small      # Opciones: tiny, base, small, medium, large-v3
AUDIO_LANGUAGE=          # Dejar vacío para auto-detección (ej: "es" para forzar español)
TMP_PATH=/app/tmp        # Usar /app/tmp si usas Docker, o /tmp en Standalone

## 📦 Modelos Disponibles

`faster-whisper` descarga automáticamente el modelo la primera vez que se ejecuta.

| Modelo | RAM Requerida | Velocidad VPS | Calidad | Recomendado para... |
|--------|--------------|---------------|---------|---------------------|
| `tiny` | ~300 MB | 🚀🚀🚀 | Básica | Pruebas |
| `base` | ~500 MB | 🚀🚀 | Buena | Audios rápidos |
| `small` | ~1.0 GB | 🚀 | Muy buena | **Uso general (Equilibrado)** |
| `medium`| ~2.5 GB | 🐢 | Excelente | Textos complejos |

*Nota: Todos los modelos usan cuantización `int8` por defecto para minimizar el consumo de RAM.*

## 🐳 Estructura de Docker Compose

Nuestro `docker-compose.yml` está diseñado para no desgastar tu disco y arrancar al instante tras reinicios:

version: '3.8'

services:
  whisper-bot:
    build: .
    container_name: telegram-whisper-bot
    restart: unless-stopped
    env_file: .env
    volumes:
      - whisper-tmp:/app/tmp
      - whisper-cache:/home/botuser/.cache/huggingface # 💾 ¡Guarda el modelo aquí!

## 🎯 Uso del bot

1. **Inicia el chat:** Envía `/start`.
2. **Envía contenido:** Mándale una Nota de Voz, un reenvío de un Vídeo o un archivo de Audio.
3. **Magia en directo:** El bot te responderá con un cronómetro: `🧠 Transcribiendo... (⏱️ 0:00:15)`.
4. **Resultado:** Recibirás tu transcripción con un resumen del tiempo tardado y el idioma detectado.

## 🛡️ Seguridad y Límites

- **Filtro de Usuarios:** Si configuras `ALLOWED_CHAT_IDS`, el bot ignorará silenciosamente a cualquier intruso.
- **Límite de Telegram:** Por limitaciones de la API de Telegram, los bots solo pueden descargar archivos de hasta **20 MB**.
- **Límite de Tiempo Interno:** El bot rechazará archivos que superen los 3600 segundos (1 hora) para no colapsar la VPS.

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!
1. Haz un **Fork** del repositorio.
2. Crea tu rama: `git checkout -b feature/nueva-funcionalidad`
3. Haz Commit: `git commit -am 'Añade nueva funcionalidad'`
4. Sube los cambios: `git push origin feature/nueva-funcionalidad`
5. Abre un **Pull Request**.

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Créditos

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Motor optimizado CTranslate2.
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Framework asíncrono para Telegram.

**¡Disfruta transcribiendo a máxima velocidad!** 🚀