import os
import time
import random
import logging
import asyncio
import gc
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from datetime import timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

# Motor optimizado
from faster_whisper import WhisperModel

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ================= DATA =================
@dataclass
class TranscriptionResult:
    text: str
    processing_time: float
    language: str
    model: str

# ================= AUDIO =================
class AudioProcessor:
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.tmp_path.mkdir(parents=True, exist_ok=True)

    async def download_audio(self, context, file_id: str) -> Path:
        audio_file = await context.bot.get_file(file_id)
        # Guardamos todo como .ogg temporalmente, Whisper se encarga de leer el formato real (mp4, wav, mp3, ogg)
        path = self.tmp_path / f"media_{random.randint(10000,99999)}.ogg"
        await audio_file.download_to_drive(custom_path=str(path))
        return path

    async def cleanup(self, *paths: Path):
        for p in paths:
            try:
                if p and p.exists():
                    p.unlink()
            except Exception as e:
                logger.error(f"Error borrando archivo {p}: {e}")

# ================= WHISPER =================
class WhisperTranscriber:
    def __init__(self, model_name="base", language=None, cpu_threads=2):
        self.model_name = model_name
        self.language = language
        
        # Configuración estricta para VPS pequeña
        self.model = WhisperModel(
            model_size_or_path=model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=cpu_threads
        )

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        start = time.time()
        
        kwargs = {
            "beam_size": 1,
            "vad_filter": True, # 🔥 Omite silencios, ahorra muchísima CPU
            "vad_parameters": dict(min_silence_duration_ms=1000)
        }
        if self.language:
            kwargs["language"] = self.language

        segments, info = self.model.transcribe(str(audio_path), **kwargs)
        
        text_parts = [segment.text.strip() for segment in segments if segment.text.strip()]
        text = " ".join(text_parts)
        
        return TranscriptionResult(
            text=text,
            processing_time=time.time() - start,
            language=info.language,
            model=self.model_name
        )

# ================= BOT =================
class TelegramWhisperBot:
    def __init__(
        self, token: str, allowed_chat_ids: List[str], tmp_path: str,
        whisper_model: str, whisper_language: Optional[str], cpu_threads: int
    ):
        self.allowed_chat_ids = set(x.strip() for x in allowed_chat_ids if x.strip())
        self.tmp_path = Path(tmp_path)
        self.audio_processor = AudioProcessor(self.tmp_path)
        
        self.transcriber = WhisperTranscriber(
            model_name=whisper_model, 
            language=whisper_language,
            cpu_threads=cpu_threads
        )
        
        self.queue = asyncio.Queue(maxsize=20)
        self.semaphore = asyncio.Semaphore(1)
        
        self.app = ApplicationBuilder().token(token).build()
        self._handlers()
        self.app.post_init = self._start_worker

# ================= WORKER =================
    async def _start_worker(self, app):
        asyncio.create_task(self._worker())

    async def _worker(self):
        while True:
            job = await self.queue.get()
            try:
                await self._process_job(**job)
            except Exception as e:
                logger.error(f"Worker error: {e}")
            finally:
                self.queue.task_done()

# ================= HANDLERS =================
    def _handlers(self):
        self.app.add_handler(CommandHandler("start", self._start))
        # Atrapa Notas de voz, Audios, Vídeos y Documentos multimedia
        self.app.add_handler(MessageHandler(
            filters.VOICE | filters.AUDIO | filters.VIDEO | filters.Document.ALL, 
            self._media, block=False
        ))

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎤 Whisper bot activo. Envíame un audio, vídeo o documento (máximo 1 hora).")

    async def _media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        if self.allowed_chat_ids and chat_id not in self.allowed_chat_ids:
            return
            
        msg = update.message
        
        # Identificar qué tipo de archivo nos han enviado
        attachment = msg.voice or msg.audio or msg.video or msg.document
        if not attachment:
            return

        # Calcular duración segura (algunos documentos pueden no tener el atributo duration)
        duration = getattr(attachment, 'duration', 0)

        if duration and duration > 3600:
            await msg.reply_text("❌ Archivo demasiado largo (máximo 1 hora)")
            return
            
        file_id = attachment.file_id
        
        try:
            self.queue.put_nowait({
                "context": context,
                "file_id": file_id,
                "chat_id": chat_id,
                "message_id": msg.message_id
            })
            await msg.reply_text("⏳ Archivo en cola... Te avisaré cuando termine.")
        except asyncio.QueueFull:
            await msg.reply_text("❌ Cola llena, espera un poco a que termine los anteriores.")

# ================= DIVISOR DE TEXTO =================
    def _split_text(self, text: str, chunk_size: int = 4000) -> List[str]:
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        safe_chunk_size = chunk_size - 30 
        
        while len(text) > safe_chunk_size:
            split_at = text.rfind(' ', 0, safe_chunk_size)
            if split_at == -1:
                split_at = safe_chunk_size
            chunks.append(text[:split_at].strip())
            text = text[split_at:].strip()
        chunks.append(text.strip())

        total = len(chunks)
        for i in range(total):
            chunks[i] = f"*[Parte {i+1}/{total}]*\n\n{chunks[i]}"
            
        return chunks

# ================= CRONÓMETRO EN VIVO =================
    async def _update_timer(self, context, chat_id, message_id, start_time):
        """Edita el mensaje cada 15s para mostrar un cronómetro en vivo"""
        try:
            while True:
                await asyncio.sleep(15)
                elapsed = int(time.time() - start_time)
                formatted_time = str(timedelta(seconds=elapsed))
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"🧠 Transcribiendo... (⏱️ {formatted_time})\n_Puedes minimizar la app, te avisaré al terminar._",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass # Ignorar errores si el texto es idéntico o hay límite de requests
        except asyncio.CancelledError:
            pass

# ================= JOB =================
    async def _process_job(self, context, file_id, chat_id, message_id):
        async with self.semaphore:
            orig = None
            status_msg = None
            timer_task = None
            start_time = time.time()
            
            try:
                status_msg = await context.bot.send_message(
                    chat_id=chat_id, 
                    text="🧠 Transcribiendo... (⏱️ 0:00:00)\n_Puedes minimizar la app, te avisaré al terminar._", 
                    reply_to_message_id=message_id,
                    parse_mode="Markdown"
                )
                
                # Lanzar el cronómetro
                timer_task = asyncio.create_task(self._update_timer(context, chat_id, status_msg.message_id, start_time))
                
                # Descargar archivo
                orig = await self.audio_processor.download_audio(context, file_id)
                
                # Procesar con Whisper
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, lambda: self.transcriber.transcribe(orig)
                )
                
                final_text = result.text if result.text else "Silencio absoluto o no pude detectar voz clara."
                
                # Detener cronómetro y limpiar el mensaje de estado
                timer_task.cancel()
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
                except Exception:
                    pass
                
                # Dividir y enviar
                mensajes = self._split_text(final_text)
                for i, mensaje_chunk in enumerate(mensajes):
                    reply_to = message_id if i == 0 else None
                    await context.bot.send_message(
                        chat_id=chat_id, 
                        text=mensaje_chunk, 
                        reply_to_message_id=reply_to,
                        parse_mode="Markdown"
                    )
                    await asyncio.sleep(0.5) 
                
                # Enviar resumen
                mins = result.processing_time / 60
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=f"⏱️ _Procesado en {mins:.1f} minutos_ | 🗣️ _{result.language}_",
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Error procesando trabajo: {e}")
                if timer_task:
                    timer_task.cancel()
                await context.bot.send_message(
                    chat_id=chat_id, text="❌ Error interno al procesar el archivo.", reply_to_message_id=message_id
                )
            finally:
                # 🧹 LIMPIEZA EXTREMA: Borrar archivo y forzar vaciado de RAM
                await self.audio_processor.cleanup(orig)
                gc.collect()

# ================= RUN =================
    def run(self):
        logger.info("🚀 Arrancando el bot en modo Polling...")
        self.app.run_polling(drop_pending_updates=True)

# ================= MAIN =================
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in environment variables")
        
    bot = TelegramWhisperBot(
        token=token,
        allowed_chat_ids=os.environ.get("ALLOWED_CHAT_IDS", "").split(","),
        tmp_path=os.environ.get("TMP_PATH", "/tmp"),
        whisper_model=os.environ.get("WHISPER_MODEL", "small"), # O el modelo que prefieras
        whisper_language=os.environ.get("AUDIO_LANGUAGE"),
        cpu_threads=max(1, os.cpu_count() // 2)
    )
    bot.run()

if __name__ == "__main__":
    main()