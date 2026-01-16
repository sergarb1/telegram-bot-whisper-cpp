import os
import time
import random
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import telegram
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from pywhispercpp.model import Model

# ================= LOGGING (MINIMO) =================
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)

# ================= DATA =================
@dataclass
class TranscriptionResult:
    text: str
    processing_time: float
    language: str
    model: str
    segments: Optional[List[Dict[str, Any]]] = None

# ================= AUDIO =================
class AudioProcessor:
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.tmp_path.mkdir(parents=True, exist_ok=True)

    async def download_audio(self, context, file_id: str) -> Path:
        audio_file = await context.bot.get_file(file_id)
        path = self.tmp_path / f"audio_{random.randint(1000,9999)}.ogg"
        await audio_file.download_to_drive(custom_path=str(path))
        return path

    async def convert_audio(self, input_path: Path) -> Path:
        wav = input_path.with_suffix(".wav")
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000",
            "-loglevel", "error", "-y", str(wav)
        ]
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError("FFmpeg failed")
        return wav

    async def cleanup(self, *paths: Path):
        for p in paths:
            try:
                if p and p.exists():
                    p.unlink()
            except Exception:
                pass

# ================= WHISPER =================
class WhisperTranscriber:
    def __init__(self, model_name="base", language=None, **params):
        self.model_name = model_name
        self.language = language
        self.model = Model(model_name, **params)

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        start = time.time()
        segments = self.model.transcribe(str(audio_path))
        text = " ".join(s.text.strip() for s in segments)
        return TranscriptionResult(
            text=text,
            processing_time=time.time() - start,
            language=self.language or "auto",
            model=self.model_name
        )

# ================= BOT =================
class TelegramWhisperBot:
    def __init__(
        self,
        token: str,
        allowed_chat_ids: List[str],
        tmp_path: str,
        whisper_model: str,
        whisper_language: Optional[str],
        whisper_params: Dict[str, Any],
    ):
        self.allowed_chat_ids = set(allowed_chat_ids)
        self.tmp_path = Path(tmp_path)

        self.audio_processor = AudioProcessor(self.tmp_path)
        self.transcriber = WhisperTranscriber(
            whisper_model,
            whisper_language,
            **whisper_params
        )

        # ---- COLA Y SEMAFORO ----
        self.queue = asyncio.Queue(maxsize=10)
        self.semaphore = asyncio.Semaphore(1)

        self.app = ApplicationBuilder().token(token).build()
        self._handlers()
        self.app.post_init = self._start_worker

    # ========== WORKER ==========
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

    # ========== HANDLERS ==========
    def _handlers(self):
        self.app.add_handler(CommandHandler("start", self._start))
        self.app.add_handler(MessageHandler(
            filters.VOICE | filters.AUDIO,
            self._audio,
            block=False
        ))

    async def _start(self, update: Update, context):
        await update.message.reply_text("🎤 Whisper bot activo")

    async def _audio(self, update: Update, context):
        chat_id = str(update.effective_chat.id)
        if self.allowed_chat_ids and chat_id not in self.allowed_chat_ids:
            return

        msg = update.message
        file_id = msg.voice.file_id if msg.voice else msg.audio.file_id

        try:
            self.queue.put_nowait({
                "update": update,
                "context": context,
                "file_id": file_id,
                "chat_id": chat_id,
                "message_id": msg.message_id
            })
            await msg.reply_text("⏳ Audio en cola…")
        except asyncio.QueueFull:
            await msg.reply_text("❌ Cola llena, espera")

    # ========== JOB ==========
    async def _process_job(self, update, context, file_id, chat_id, message_id):
        async with self.semaphore:
            orig = wav = None
            try:
                orig = await self.audio_processor.download_audio(context, file_id)
                wav = await self.audio_processor.convert_audio(orig)

                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.transcriber.transcribe(wav)
                )

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=result.text,
                    reply_to_message_id=message_id
                )
            finally:
                await self.audio_processor.cleanup(orig, wav)

    def run(self):
        self.app.run_polling(drop_pending_updates=True)

# ================= MAIN =================
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN")

    bot = TelegramWhisperBot(
        token=token,
        allowed_chat_ids=os.environ.get("ALLOWED_CHAT_IDS", "").split(","),
        tmp_path=os.environ.get("TMP_PATH", "/tmp/whisper_bot"),
        whisper_model=os.environ.get("WHISPER_MODEL", "base"),
        whisper_language=os.environ.get("AUDIO_LANGUAGE"),
        whisper_params={
            "n_threads": 2,
            "print_realtime": False,
            "print_progress": False,
            "no_context": True,
        }
    )
    bot.run()

if __name__ == "__main__":
    main()
