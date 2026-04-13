# 🤖 Telegram Bot Whisper (Powered by Faster-Whisper)

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Faster-Whisper](https://img.shields.io/badge/Faster--Whisper-Optimized-FF6B6B.svg?style=flat-square)](https://github.com/SYSTRAN/faster-whisper)

Un bot de Telegram extremadamente optimizado que transcribe notas de voz, vídeos y archivos de audio a texto usando **Faster-Whisper** (CTranslate2). Totalmente auto-alojado, privado y diseñado para exprimir al máximo servidores VPS con recursos limitados.

---

## 📋 Tabla de Contenidos
- [✨ Características](#-características)
- [🛠️ Requisitos Previos](#️-requisitos-previos)
- [🚀 Instalación Rápida (Docker)](#-instalación-rápida-docker)
- [💻 Instalación Manual (Standalone)](#-instalación-manual-standalone)
- [🔧 Configuración (.env)](#-configuración-env)
- [📦 Comparativa de Modelos](#-comparativa-de-modelos)
- [🎯 Uso del Bot](#-uso-del-bot)
- [🛡️ Seguridad y Límites](#-seguridad-y-límites)
- [🤝 Contribuir](#-contribuir)

---

## ✨ Características

- 🎤 **Motor Ultrarrápido:** Migrado a `faster-whisper` con cuantización INT8, hasta 4 veces más rápido que Whisper original.
- 🔇 **Filtro VAD Inteligente:** Elimina silencios y ruidos de fondo *antes* de procesar, ahorrando hasta un 30% de CPU.
- ⏱️ **Cronómetro en vivo:** Edita su propio mensaje cada 15s para mostrarte el tiempo de procesamiento en directo.
- ✂️ **Divisor Automático de Textos:** Soporta audios largos (hasta 1 hora). Si el texto supera el límite de Telegram (4096 caracteres), lo envía ordenadamente en fragmentos como `[Parte 1/3]`.
- 🧹 **Gestión Extrema de RAM:** Fuerza la recolección de basura (Garbage Collection) tras cada transcripción para evitar cuelgues en servidores pequeños.
- 🎬 **Soporte Multimedia:** Acepta Notas de Voz, Audios MP3/WAV, Vídeos MP4 y Documentos.
- 🐳 **Docker Optimizado:** Incluye volumen de caché para que los modelos no se descarguen cada vez que reinicias.

---

## 🛠️ Requisitos Previos

Antes de empezar, asegúrate de tener:
1. **Telegram Bot Token:** Consíguelo hablando con [@BotFather](https://t.me/BotFather).
2. **Tu ID de Telegram:** Puedes obtenerlo con [@userinfobot](https://t.me/userinfobot) (opcional, para restringir el acceso).
3. **Hardware:** Mínimo 1GB de RAM libre (recomendado 2GB+ para el modelo `small`).

---

## 🚀 Instalación Rápida (Docker)

Esta es la forma recomendada para la mayoría de los usuarios.

```bash
# 1. Clona el repositorio
git clone https://github.com/tuusuario/telegram-whisper-bot.git
cd telegram-whisper-bot

# 2. Configura las variables de entorno
cp .env.example .env
nano .env  # Añade tu TELEGRAM_BOT_TOKEN

# 3. Construye e inicia el bot
docker-compose up -d --build

# 4. Verifica los logs
docker-compose logs -f
```

---

## 💻 Instalación Manual (Standalone)

Si prefieres no usar Docker, asegúrate de tener **Python 3.11+** y **FFmpeg** instalado.

```bash
# Instala FFmpeg (Ejemplo en Debian/Ubuntu)
sudo apt update && sudo apt install -y ffmpeg

# 1. Clona el repositorio
git clone https://github.com/tuusuario/telegram-whisper-bot.git
cd telegram-whisper-bot

# 2. Instala las dependencias
pip install -r requirements.txt

# 3. Configura el script de arranque o usa .env
cp .env.example .env
nano .env

# 4. Ejecuta el bot
python telegram_whisper_bot.py
```

---

## 🔧 Configuración (`.env`)

Crea un archivo `.env` en la raíz del proyecto. Estas son las opciones disponibles:

| Variable | Descripción | Valor Recomendado |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Token de @BotFather | (Requerido) |
| `ALLOWED_CHAT_IDS` | IDs permitidos (separados por comas) | Vacío = Público |
| `WHISPER_MODEL` | Tamaño del modelo (tiny, base, small, medium) | `small` |
| `AUDIO_LANGUAGE` | Idioma forzado (es, en, fr...) | Vacío (Auto-detección) |
| `TMP_PATH` | Ruta para archivos temporales | `/app/tmp` (Docker) |
| `WHISPER_TRANSLATE` | Traducir audio al inglés automáticamente | `false` |

---

## 📦 Comparativa de Modelos

`faster-whisper` descarga automáticamente el modelo la primera vez.

| Modelo | RAM (Aprox) | Velocidad | Calidad | Recomendación |
| :--- | :---: | :---: | :---: | :--- |
| `tiny` | ~300 MB | 🚀🚀🚀 | Básica | Pruebas / VPS Muy pequeñas |
| `base` | ~500 MB | 🚀🚀 | Buena | Audios cortos y claros |
| `small` | **~1.0 GB** | 🚀 | **Muy buena** | **Recomendado (Equilibrado)** |
| `medium`| ~2.5 GB | 🐢 | Excelente | Textos complejos / Transcripción fiel |

> **Nota:** Todos los modelos usan cuantización `int8` por defecto para minimizar el consumo de RAM sin perder precisión.

---

## 🎯 Uso del Bot

1.  **Inicia el chat:** Envía `/start`.
2.  **Envía contenido:** Mándale una Nota de Voz, un Vídeo o un archivo de Audio.
3.  **Procesamiento:** El bot mostrará un cronómetro en tiempo real: `🧠 Transcribiendo... (⏱️ 0:00:15)`.
4.  **Resultado:** Recibirás la transcripción completa, el tiempo total y el idioma detectado.

---

## 🛡️ Seguridad y Límites

-   **Filtro de Usuarios:** Si configuras `ALLOWED_CHAT_IDS`, el bot ignorará cualquier mensaje de otros usuarios.
-   **Límite de Archivo (Telegram):** Máximo **20 MB** por archivo debido a limitaciones de la API oficial de bots.
-   **Límite de Tiempo:** El bot está configurado para rechazar archivos de más de **1 hora** para evitar bloqueos del servidor.

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!
1. Haz un **Fork** del repositorio.
2. Crea tu rama: `git checkout -b feature/nueva-funcionalidad`
3. Haz Commit: `git commit -am 'Añade nueva funcionalidad'`
4. Sube los cambios: `git push origin feature/nueva-funcionalidad`
5. Abre un **Pull Request**.

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Créditos

-   [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - El motor optimizado basado en CTranslate2.
-   [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - El framework asíncrono para Telegram.

---
**¡Disfruta transcribiendo a máxima velocidad!** 🚀
