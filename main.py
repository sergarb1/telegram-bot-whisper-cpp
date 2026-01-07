#!/usr/bin/env python3
"""
Telegram Bot for audio transcription using pywhispercpp
Optimized for performance and reliability
"""

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
from telegram import Update, Message
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from pywhispercpp.model import Model

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """Dataclass to store transcription results"""
    text: str
    processing_time: float
    language: str
    model: str
    segments: Optional[List[Dict[str, Any]]] = None

class AudioProcessor:
    """Handles audio file processing and cleanup"""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.tmp_path.mkdir(parents=True, exist_ok=True)

    async def download_audio(self, context: ContextTypes.DEFAULT_TYPE, file_id: str) -> Path:
        """Download audio file from Telegram"""
        audio_file = await context.bot.get_file(file_id)
        audio_path = self.tmp_path / f"audio_{random.randint(1000, 9999)}.ogg"
        await audio_file.download_to_drive(custom_path=str(audio_path))
        return audio_path

    async def convert_audio(self, input_path: Path) -> Path:
        """Convert audio to WAV format for Whisper"""
        wav_path = input_path.with_suffix('.wav')

        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-acodec', 'pcm_s16le',
            '-ac', '1',
            '-ar', '16000',
            '-loglevel', 'error',
            '-y',
            str(wav_path)
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                raise RuntimeError(f"Audio conversion failed")

            return wav_path

        except Exception as e:
            logger.error(f"Conversion error: {e}")
            raise

    async def cleanup(self, *paths: Path):
        """Clean up temporary files"""
        for path in paths:
            try:
                if path and path.exists():
                    path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete {path}: {e}")

class WhisperTranscriber:
    """Handles Whisper transcription using pywhispercpp"""

    def __init__(
        self,
        model_name: str = "base",
        language: Optional[str] = None,
        n_threads: Optional[int] = None,
        print_realtime: bool = False,
        print_progress: bool = False,
        **kwargs
    ):
        self.model_name = model_name
        self.language = language
        self.n_threads = n_threads
        self.print_realtime = print_realtime
        self.print_progress = print_progress
        self.extra_params = kwargs

        logger.info(f"Initializing Whisper model: {model_name}")

        # Prepare model parameters
        model_params = {
            'print_realtime': print_realtime,
            'print_progress': print_progress,
            **kwargs
        }

        if n_threads:
            model_params['n_threads'] = n_threads

        # Initialize model
        try:
            self.model = Model(model_name, **model_params)
            logger.info(f"Model {model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        translate: bool = False,
        no_context: bool = True,
        **transcribe_kwargs
    ) -> TranscriptionResult:
        """Transcribe audio file with detailed results"""
        try:
            start_time = time.time()

            # Prepare transcription parameters
            params = {
                'translate': translate,
                'no_context': no_context,
                **transcribe_kwargs
            }

            # Set language if specified
            if language:
                params['language'] = language
            elif self.language and self.language != "auto":
                params['language'] = self.language

            # Transcribe audio
            segments = self.model.transcribe(str(audio_path), **params)

            # Combine segment texts
            full_text = ' '.join([segment.text.strip() for segment in segments])

            processing_time = time.time() - start_time

            # Prepare segment details (usando atributos correctos)
            segment_details = []
            for idx, segment in enumerate(segments):
                try:
                    # Intentar acceder a los atributos comunes
                    segment_info = {
                        'text': segment.text.strip(),
                        'id': idx,  # Usamos índice en lugar de atributo id
                    }

                    # Verificar si tiene atributos de tiempo (pueden variar según versión)
                    if hasattr(segment, 't0'):
                        segment_info['start'] = segment.t0
                    if hasattr(segment, 't1'):
                        segment_info['end'] = segment.t1

                    segment_details.append(segment_info)
                except AttributeError as e:
                    logger.warning(f"Segment attribute error: {e}")
                    # Continuar sin este segmento detallado
                    continue

            return TranscriptionResult(
                text=full_text,
                processing_time=processing_time,
                language=params.get('language', 'auto'),
                model=self.model_name,
                segments=segment_details if segment_details else None
            )

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            raise

class TelegramWhisperBot:
    """Main Telegram bot class for Whisper transcription"""

    def __init__(
        self,
        token: str,
        allowed_chat_ids: List[str],
        tmp_path: str,
        whisper_model: str = "base",
        whisper_language: Optional[str] = None,
        whisper_params: Optional[Dict[str, Any]] = None
    ):
        self.token = token
        self.allowed_chat_ids = set(allowed_chat_ids)
        self.tmp_path = Path(tmp_path)

        # Default Whisper parameters
        default_params = {
            'n_threads': min(4, os.cpu_count() or 1),
            'print_realtime': False,
            'print_progress': False,
            'no_context': True,
            'translate': False
        }

        if whisper_params:
            default_params.update(whisper_params)

        # Initialize components
        self.audio_processor = AudioProcessor(self.tmp_path)
        self.transcriber = WhisperTranscriber(
            model_name=whisper_model,
            language=whisper_language,
            **default_params
        )

        # Build application
        self.application = ApplicationBuilder().token(token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_handler))
        self.application.add_handler(CommandHandler("help", self._help_handler))
        self.application.add_handler(CommandHandler("status", self._status_handler))
        self.application.add_handler(CommandHandler("model", self._model_handler))

        # Message handlers
        self.application.add_handler(
            MessageHandler(
                filters.VOICE | filters.AUDIO,
                self._audio_handler,
                block=False
            )
        )

    async def _check_permission(self, chat_id: str) -> bool:
        """Check if chat is allowed"""
        if not self.allowed_chat_ids:
            logger.warning("No allowed chats configured, denying all")
            return False
        return str(chat_id) in self.allowed_chat_ids

    @staticmethod
    def _escape_markdown(text: str) -> str:
        """Escape special characters for Telegram MarkdownV2"""
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text

    @staticmethod
    def _split_text(text: str, max_length: int = 4000) -> List[str]:
        """Split text into chunks respecting max length"""
        chunks = []
        while text:
            # Find a good break point near max_length
            if len(text) <= max_length:
                chunks.append(text)
                break

            # Try to break at sentence end
            break_point = text.rfind('. ', 0, max_length)
            if break_point == -1:
                # Try to break at word boundary
                break_point = text.rfind(' ', 0, max_length)
                if break_point == -1:
                    # Force break
                    break_point = max_length

            chunks.append(text[:break_point + 1].strip())
            text = text[break_point + 1:].strip()

        return chunks

    def _format_transcription(self, result: TranscriptionResult) -> str:
        # For custom format of result, default plain text
        header=""
        metadata=""
        return header + metadata + result.text

    async def _start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = update.effective_chat.id

        if not await self._check_permission(chat_id):
            await update.message.reply_text("❌ Sorry, you don't have permission to use this bot.")
            return

        welcome_msg = (
            "🎤 *Whisper Transcription Bot*\n\n"
            "Send me an audio message or audio file, and I'll transcribe it for you.\n\n"
            "*Commands:*\n"
            "/start - Show this message\n"
            "/help - Show help\n"
            "/status - Check bot status\n"
            "/model - Show current model info\n\n"
            f"*Current settings:*\n"
            f"• Model: `{self.transcriber.model_name}`\n"
            f"• Language: `{self.transcriber.language or 'auto'}`\n"
            f"• Threads: `{self.transcriber.n_threads}`"
        )

        await update.message.reply_text(
            self._escape_markdown(welcome_msg),
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
        )

    async def _help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_msg = (
            "*How to use:*\n"
            "1. Send an audio message or audio file\n"
            "2. Wait for transcription\n"
            "3. Receive formatted result\n\n"
            "*Supported formats:*\n"
            "• Audio messages (OGG)\n"
            "• Audio files (MP3, M4A, WAV, etc.)\n\n"
            "*Requirements:*\n"
            "• FFmpeg must be installed on the server\n"
            "• Max file size: 20MB (Telegram limit)\n\n"
            "*Note:* Large files or long recordings may take longer to process."
        )

        await update.message.reply_text(
            self._escape_markdown(help_msg),
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
        )

    async def _status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        import shutil

        try:
            # Get disk usage
            total, used, free = shutil.disk_usage(self.tmp_path)

            status_msg = (
                "*Bot Status*\n\n"
                f"• Model: `{self.transcriber.model_name}`\n"
                f"• Language: `{self.transcriber.language or 'auto'}`\n"
                f"• Temp folder: `{self.tmp_path}`\n"
                f"• Disk free: `{free // (1024**3)} GB`\n"
                f"• Allowed chats: `{len(self.allowed_chat_ids)}`\n"
                f"• Status: ✅ Online"
            )

        except Exception as e:
            status_msg = f"*Status*\n\nError getting status: {str(e)[:100]}"

        await update.message.reply_text(
            self._escape_markdown(status_msg),
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
        )

    async def _model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /model command"""
        model_msg = (
            "*Model Information*\n\n"
            f"• Name: `{self.transcriber.model_name}`\n"
            f"• Language: `{self.transcriber.language or 'auto'}`\n"
            f"• Threads: `{self.transcriber.n_threads}`\n"
            f"• Real-time output: `{self.transcriber.print_realtime}`\n"
            f"• Progress display: `{self.transcriber.print_progress}`\n\n"
            "*Available models:*\n"
            "• tiny (~75MB)\n"
            "• base (~142MB)\n"
            "• small (~466MB)\n"
            "• medium (~1.5GB)\n"
            "• large (~3.1GB)\n\n"
            "Add `.en` for English-only models"
        )

        await update.message.reply_text(
            self._escape_markdown(model_msg),
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
        )

    async def _audio_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming audio messages"""
        chat_id = update.effective_chat.id
        message_id = update.message.message_id

        # Check permissions
        if not await self._check_permission(chat_id):
            logger.warning(f"Unauthorized access attempt from chat {chat_id}")
            return

        # Get file info
        if update.message.voice:
            file_id = update.message.voice.file_id
            file_size = update.message.voice.file_size
            duration = update.message.voice.duration
        elif update.message.audio:
            file_id = update.message.audio.file_id
            file_size = update.message.audio.file_size
            duration = getattr(update.message.audio, 'duration', 0)
        else:
            return

        logger.info(f"Processing audio: chat={chat_id}, size={file_size}, duration={duration}s")

        # Check file size (Telegram limit is 20MB for bots)
        if file_size and file_size > 20 * 1024 * 1024:
            await update.message.reply_text(
                "❌ File too large. Maximum size is 20MB.",
                reply_to_message_id=message_id
            )
            return

        original_path = None
        wav_path = None

        try:
            # Set typing action
            await context.bot.send_chat_action(
                chat_id=chat_id,
                action=telegram.constants.ChatAction.TYPING
            )

            original_path = await self.audio_processor.download_audio(context, file_id)
            wav_path = await self.audio_processor.convert_audio(original_path)
            # Run transcription in thread pool
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.transcriber.transcribe(wav_path)
            )

            # Format and send result
            formatted_text = self._format_transcription(result)
            escaped_text = self._escape_markdown(formatted_text)

            # Split long messages
            chunks = self._split_text(escaped_text)

            for i, chunk in enumerate(chunks):
                if i == 0:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=chunk,
                        reply_to_message_id=message_id,
                        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=chunk,
                        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                    )

            logger.info(f"Successfully transcribed audio in {result.processing_time:.1f}s")

        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)

            error_msg = (
                "❌ *Processing Error*\n\n"
                "Failed to transcribe audio. Please try again.\n"
                f"Error: `{str(e)[:200]}`"
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=self._escape_markdown(error_msg),
                reply_to_message_id=message_id,
                parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
            )

        finally:
            # Cleanup temporary files
            await self.audio_processor.cleanup(original_path, wav_path)

    def run(self):
        """Start the bot"""
        logger.info("Starting Whisper Telegram Bot...")
        logger.info(f"Model: {self.transcriber.model_name}")
        logger.info(f"Language: {self.transcriber.language or 'auto'}")
        logger.info(f"Allowed chats: {len(self.allowed_chat_ids)}")
        logger.info(f"Temp path: {self.tmp_path}")

        if not self.allowed_chat_ids:
            logger.warning("WARNING: No allowed chats configured. Bot will not process any messages.")

        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            logger.info("FFmpeg is available")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("FFmpeg is not available or not in PATH. Audio conversion will fail!")

        self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )

def load_config():
    """Load configuration from environment variables"""
    config = {
        'token': os.environ.get("TELEGRAM_BOT_TOKEN"),
        'allowed_chats': os.environ.get("ALLOWED_CHAT_IDS", "").split(","),
        'tmp_path': os.environ.get("TMP_PATH", "/tmp/telegram_whisper_bot"),
        'model': os.environ.get("WHISPER_MODEL", "base"),
        'language': os.environ.get("AUDIO_LANGUAGE", None),
        'n_threads': os.environ.get("WHISPER_THREADS"),
        'translate': os.environ.get("WHISPER_TRANSLATE", "false").lower() == "true",
    }

    # Filter empty chat IDs
    config['allowed_chats'] = [cid.strip() for cid in config['allowed_chats'] if cid.strip()]

    # Parse threads if provided
    if config['n_threads']:
        try:
            config['n_threads'] = int(config['n_threads'])
        except ValueError:
            config['n_threads'] = None

    # Parse language (empty string means auto)
    if config['language'] == "":
        config['language'] = None

    return config

def main():
    """Main entry point"""
    # Load configuration
    config = load_config()

    # Validate token
    if not config['token']:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is required")
        exit(1)

    # Prepare Whisper parameters
    whisper_params = {
        'n_threads': config['n_threads'],
        'translate': config['translate'],
    }

    # Create and run bot
    bot = TelegramWhisperBot(
        token=config['token'],
        allowed_chat_ids=config['allowed_chats'],
        tmp_path=config['tmp_path'],
        whisper_model=config['model'],
        whisper_language=config['language'],
        whisper_params=whisper_params
    )

    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
