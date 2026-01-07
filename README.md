# 🤖 Telegram Bot para Transcribir Audio con Whisper AI

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Whisper.cpp](https://img.shields.io/badge/Whisper.cpp-Powered-FF6B6B.svg)

Un bot de Telegram que transcribe notas de voz y archivos de audio a texto usando **pywhispercpp** (bindings Python para whisper.cpp). Totalmente auto-alojado, privado y de alto rendimiento.

## ✨ Características

- 🎤 **Transcripción local** - Todo el procesamiento ocurre en tu servidor
- 🔒 **100% privado** - Sin datos enviados a servicios externos
- ⚡ **Alto rendimiento** - Usa whisper.cpp optimizado en C++
- 🎯 **Múltiples modelos** - Desde `tiny` (75MB) hasta `large` (3.1GB)
- 🌍 **Detección automática de idioma** - Soporta 99+ idiomas
- 🐳 **Docker incluido** - Fácil despliegue en cualquier servidor
- 📱 **Soporta varios formatos** - Notas de voz, MP3, M4A, WAV, etc.
- 🛡️ **Sistema de permisos** - Solo usuarios autorizados pueden usarlo

## 🚀 Empezar rápidamente

### Con Docker (recomendado)

```bash
# 1. Clona el repositorio
git clone https://github.com/tuusuario/telegram-whisper-bot.git
cd telegram-whisper-bot

# 2. Configura las variables de entorno
cp .env.example .env
nano .env  # Edita con tus credenciales

# 3. Inicia el bot
docker-compose up -d

# 4. Verifica que está funcionando
docker-compose logs -f
```

### Instalación manual

```bash
# 1. Instala dependencias del sistema
sudo apt update && sudo apt install python3 python3-pip ffmpeg -y

# 2. Clona el repositorio
git clone https://github.com/tuusuario/telegram-whisper-bot.git
cd telegram-whisper-bot

# 3. Instala dependencias de Python
pip install -r requirements.txt

# 4. Configura el bot
export TELEGRAM_BOT_TOKEN="tu_token_aqui"
export ALLOWED_CHAT_IDS="123456789"

# 5. Ejecuta el bot
python telegram_whisper_bot.py
```

## 🔧 Configuración

### 1. Crear un bot en Telegram

1. Abre Telegram y busca [@BotFather](https://t.me/botfather)
2. Envía `/newbot` y sigue las instrucciones
3. Guarda el **token** que te proporcionen

### 2. Obtener IDs de chat

| Para... | Cómo obtener el ID |
|---------|-------------------|
| **Usuario** | Habla con [@userinfobot](https://t.me/userinfobot) |
| **Grupo** | Añade [@RawDataBot](https://t.me/RawDataBot) al grupo |
| **Canal** | Reenvía mensaje del canal a [@RawDataBot](https://t.me/RawDataBot) |

### 3. Archivo `.env`

Crea un archivo `.env` basado en `.env.example`:

```env
# REQUERIDO: Token del bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# OPCIONAL: IDs permitidos (separados por comas)
ALLOWED_CHAT_IDS=123456789,987654321

# Configuración de Whisper
WHISPER_MODEL=base            # Modelo a usar
AUDIO_LANGUAGE=               # Dejar vacío para auto-detección
WHISPER_THREADS=4             # Número de hilos CPU
TMP_PATH=/tmp/whisper_bot     # Carpeta temporal
```

## 📦 Modelos disponibles

| Modelo | Tamaño | RAM | CPU | Calidad | Uso recomendado |
|--------|--------|-----|-----|---------|-----------------|
| `tiny` | 75 MB | ~390 MB | ⭐⭐ | Adecuada | Pruebas, dispositivos limitados |
| `base` | 142 MB | ~500 MB | ⭐⭐⭐ | Buena | Uso general (default) |
| `small` | 466 MB | ~1 GB | ⭐⭐⭐⭐ | Muy buena | Alta precisión |
| `medium` | 1.5 GB | ~2.7 GB | ⭐⭐⭐⭐⭐ | Excelente | Transcripciones profesionales |
| `large` | 3.1 GB | ~4.7 GB | ⭐⭐⭐⭐⭐⭐ | Superior | Máxima precisión, investigación |

**Tip**: Para solo inglés, usa modelos `.en` (ej: `base.en`)

## 🎯 Uso del bot

### Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `/start` | Muestra información del bot |
| `/help` | Muestra ayuda de uso |
| `/status` | Ver estado del bot |
| `/model` | Información del modelo actual |

### Cómo transcribir

1. **Envía una nota de voz** al bot
2. **Espera** mientras procesa:
   - ⬇️ Descargando audio...
   - 🔄 Convirtiendo a WAV...
   - 🤖 Transcribiendo con Whisper...
3. **Recibe** la transcripción

### Ejemplo de salida

```
Hola, esta es una nota de voz de prueba
para verificar que el bot funciona correctamente.
```

## 🐳 Docker

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  whisper-bot:
    build: .
    container_name: telegram-whisper-bot
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - ALLOWED_CHAT_IDS=${ALLOWED_CHAT_IDS}
      - WHISPER_MODEL=${WHISPER_MODEL:-base}
      - TMP_PATH=/tmp/whisper_bot
    volumes:
      - whisper-tmp:/tmp/whisper_bot

volumes:
  whisper-tmp:
```

### Comandos Docker útiles

```bash
# Construir imagen
docker build -t whisper-telegram-bot .

# Ejecutar
docker run -d \
  --name whisper-bot \
  -e TELEGRAM_BOT_TOKEN="tu_token" \
  whisper-telegram-bot

# Ver logs
docker logs -f whisper-bot

# Acceder al contenedor
docker exec -it whisper-bot /bin/sh
```

## ⚡ Optimización de rendimiento

### Para CPU

```bash
# Instalar con OpenBLAS para mejor rendimiento
GGML_BLAS=1 pip install pywhispercpp --no-cache-dir --force-reinstall

# Usar más hilos (ajusta según tu CPU)
export WHISPER_THREADS=$(nproc)
```

### Para GPU NVIDIA

```bash
# Instalar con soporte CUDA
GGML_CUDA=1 pip install pywhispercpp --no-cache-dir --force-reinstall
```

### Para macOS

```bash
# Instalar con soporte CoreML
WHISPER_COREML=1 pip install pywhispercpp --no-cache-dir --force-reinstall
```

## 📊 Requisitos del sistema

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| **RAM** | 512 MB | 2 GB+ |
| **CPU** | 1 núcleo | 4+ núcleos |
| **Disco** | 500 MB | 5 GB+ |
| **Python** | 3.8+ | 3.11+ |
| **FFmpeg** | 4.0+ | 5.0+ |

## 🔧 Solución de problemas

### Error común: "FFmpeg no encontrado"

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (chocolatey)
choco install ffmpeg
```

### Error: "No tengo permiso para usar el bot"

Verifica que:
1. Tu ID de chat está en `ALLOWED_CHAT_IDS`
2. El ID es correcto (puede ser negativo para grupos)
3. No hay espacios en blanco en la lista

### Error: "Memoria insuficiente"

```bash
# Usa un modelo más pequeño
export WHISPER_MODEL=tiny

# Reduce número de hilos
export WHISPER_THREADS=2

# Aumenta swap (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Error: "Timeout al descargar modelo"

Descarga manualmente:
1. Visita: https://huggingface.co/ggerganov/whisper.cpp
2. Descarga el modelo GGML
3. Colócalo en: `~/.cache/whisper/`

## 🛡️ Seguridad

- ✅ **Lista blanca de usuarios** - Solo chats autorizados
- ✅ **Límite de tamaño** - Máximo 20MB (límite de Telegram)
- ✅ **Sin almacenamiento** - Archivos temporales se eliminan
- ✅ **Tokens seguros** - Variables de entorno, no en código
- ✅ **Actualizaciones** - Dependencias mantenidas

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. **Fork** el repositorio
2. **Crea una rama**: `git checkout -b feature/nueva-funcionalidad`
3. **Commit**: `git commit -am 'Añade nueva funcionalidad'`
4. **Push**: `git push origin feature/nueva-funcionalidad`
5. **Abre un Pull Request**

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Créditos

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Georgi Gerganov
- [pywhispercpp](https://github.com/absadiki/pywhispercpp) - Python bindings
- [python-telegram-bot](https://github.com/python-telegram-bot) - Biblioteca del bot
- Inspirado en varios proyectos de código abierto

## 🌟 Estrellas

Si este proyecto te resulta útil, ¡dale una estrella ⭐ en GitHub!

## 📞 Soporte

- **Issues**: [Reportar problemas](https://github.com/tuusuario/telegram-whisper-bot/issues)
- **Discusiones**: [Foro de ayuda](https://github.com/tuusuario/telegram-whisper-bot/discussions)


**Nota**: Para uso comercial o alto volumen, considera monitorear el uso de recursos y ajustar la configuración según tus necesidades.

**¡Disfruta transcribiendo!** 🎤 → 📝
