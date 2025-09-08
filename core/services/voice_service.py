"""
Сервис обработки голосовых сообщений
Обеспечивает STT (Speech-to-Text) функционал для AI-помощника
"""

import os
import tempfile
import logging
import asyncio
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import Voice, Audio, Message
from core.settings import settings

logger = logging.getLogger(__name__)

class VoiceService:
    """Сервис обработки голосовых сообщений"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "karma_voice"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Rate limiting storage (in production should use Redis)
        self._rate_limits = {}
        
        # Initialize STT models
        self._stt_model = None
        self._init_stt_model()
    
    def _init_stt_model(self):
        """Инициализация модели STT"""
        try:
            # Try faster-whisper first (recommended)
            from faster_whisper import WhisperModel
            self._stt_model = WhisperModel("small", device="cpu", compute_type="int8")
            logger.info("✅ Faster-whisper model loaded successfully")
        except ImportError:
            try:
                # Fallback to vosk
                import vosk
                self._stt_model = "vosk"
                logger.info("✅ Vosk model will be used as fallback")
            except ImportError:
                logger.warning("⚠️ No STT models available. Install faster-whisper or vosk")
                self._stt_model = None
    
    async def check_rate_limit(self, user_id: int) -> bool:
        """Проверка rate limit для пользователя"""
        now = datetime.now()
        user_key = str(user_id)
        
        if user_key not in self._rate_limits:
            self._rate_limits[user_key] = []
        
        # Clean old requests
        cutoff = now - timedelta(seconds=settings.voice.rate_period)
        self._rate_limits[user_key] = [
            req_time for req_time in self._rate_limits[user_key] 
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self._rate_limits[user_key]) >= settings.voice.rate_limit:
            return False
        
        # Add current request
        self._rate_limits[user_key].append(now)
        return True
    
    async def validate_voice_message(self, message: Message) -> Tuple[bool, Optional[str]]:
        """Валидация голосового сообщения"""
        voice = message.voice or message.audio
        
        if not voice:
            return False, "No voice/audio found"
        
        # Check duration
        if voice.duration > settings.voice.max_duration:
            return False, "too_long"
        
        # Check file size
        max_size_bytes = settings.voice.max_filesize_mb * 1024 * 1024
        if voice.file_size and voice.file_size > max_size_bytes:
            return False, "too_large"
        
        return True, None
    
    async def download_voice_file(self, bot: Bot, voice: Voice | Audio) -> Optional[Path]:
        """Скачивание голосового файла"""
        try:
            # Get file info
            file_info = await bot.get_file(voice.file_id)
            
            # Create temp file
            temp_file = self.temp_dir / f"voice_{voice.file_id}_{datetime.now().timestamp()}.ogg"
            
            # Download file
            await bot.download_file(file_info.file_path, temp_file)
            
            logger.info(f"✅ Voice file downloaded: {temp_file}")
            return temp_file
            
        except Exception as e:
            logger.error(f"Error downloading voice file: {e}")
            return None
    
    async def convert_to_wav(self, input_file: Path) -> Optional[Path]:
        """Конвертация аудио в WAV формат"""
        try:
            import ffmpeg
            
            output_file = input_file.with_suffix('.wav')
            
            # Convert to 16kHz mono WAV
            (
                ffmpeg
                .input(str(input_file))
                .output(
                    str(output_file),
                    acodec='pcm_s16le',
                    ac=1,  # mono
                    ar=16000  # 16kHz
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            logger.info(f"✅ Audio converted to WAV: {output_file}")
            return output_file
            
        except ImportError:
            logger.error("ffmpeg-python not installed")
            return None
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return None
    
    async def transcribe_audio(self, audio_file: Path) -> Tuple[Optional[str], Optional[str]]:
        """Транскрибация аудио в текст"""
        if not self._stt_model:
            return None, "STT model not available"
        
        try:
            if isinstance(self._stt_model, str) and self._stt_model == "vosk":
                return await self._transcribe_vosk(audio_file)
            else:
                return await self._transcribe_faster_whisper(audio_file)
                
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None, "transcription_error"
    
    async def _transcribe_faster_whisper(self, audio_file: Path) -> Tuple[Optional[str], Optional[str]]:
        """Транскрибация с помощью faster-whisper"""
        try:
            segments, info = self._stt_model.transcribe(str(audio_file))
            
            # Combine all segments
            text = " ".join([segment.text for segment in segments])
            
            # Detect language
            detected_lang = info.language
            
            logger.info(f"✅ Transcription completed: {len(text)} chars, lang: {detected_lang}")
            return text.strip(), detected_lang
            
        except Exception as e:
            logger.error(f"Faster-whisper transcription error: {e}")
            return None, "transcription_error"
    
    async def _transcribe_vosk(self, audio_file: Path) -> Tuple[Optional[str], Optional[str]]:
        """Транскрибация с помощью Vosk (fallback)"""
        try:
            import vosk
            import json
            
            # Load model (you need to download models separately)
            model_path = os.getenv("VOSK_MODEL_PATH", "vosk-model-small-ru-0.22")
            if not os.path.exists(model_path):
                logger.error(f"Vosk model not found at {model_path}")
                return None, "model_not_found"
            
            model = vosk.Model(model_path)
            rec = vosk.KaldiRecognizer(model, 16000)
            
            # Read audio file
            with open(audio_file, 'rb') as f:
                while True:
                    data = f.read(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        pass
            
            result = json.loads(rec.FinalResult())
            text = result.get('text', '')
            
            logger.info(f"✅ Vosk transcription completed: {len(text)} chars")
            return text.strip(), "ru"  # Default to Russian for Vosk
            
        except Exception as e:
            logger.error(f"Vosk transcription error: {e}")
            return None, "transcription_error"
    
    async def cleanup_temp_files(self, *files: Path):
        """Очистка временных файлов"""
        for file_path in files:
            try:
                if file_path and file_path.exists():
                    file_path.unlink()
                    logger.debug(f"🗑️ Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {e}")
    
    async def process_voice_message(self, bot: Bot, message: Message) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Полная обработка голосового сообщения
        
        Returns:
            Tuple[text, language, error_code]
        """
        try:
            # Validate message
            is_valid, error_code = await self.validate_voice_message(message)
            if not is_valid:
                return None, None, error_code
            
            # Check rate limit
            if not await self.check_rate_limit(message.from_user.id):
                return None, None, "rate_limit"
            
            # Get voice/audio object
            voice = message.voice or message.audio
            
            # Download file
            temp_file = await self.download_voice_file(bot, voice)
            if not temp_file:
                return None, None, "download_error"
            
            # Convert to WAV
            wav_file = await self.convert_to_wav(temp_file)
            if not wav_file:
                await self.cleanup_temp_files(temp_file)
                return None, None, "conversion_error"
            
            # Transcribe
            text, language = await self.transcribe_audio(wav_file)
            
            # Cleanup
            await self.cleanup_temp_files(temp_file, wav_file)
            
            if not text:
                return None, None, "couldnt_understand"
            
            logger.info(f"✅ Voice processing completed for user {message.from_user.id}: {len(text)} chars")
            return text, language, None
            
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            return None, None, "processing_error"

# Global instance
voice_service = VoiceService()
