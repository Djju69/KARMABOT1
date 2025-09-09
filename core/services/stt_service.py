"""
Сервис распознавания речи для AI-ассистента
"""
import logging
import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class STTService:
    """Сервис для распознавания речи"""
    
    def __init__(self):
        self.supported_formats = ['.ogg', '.mp3', '.m4a', '.wav']
        self.max_duration = 60  # секунд
        self.max_size_mb = 2    # МБ
    
    async def prepare_audio(self, message) -> tuple[str, Dict[str, Any]]:
        """
        Подготавливает аудиофайл для обработки
        """
        try:
            # Получаем файл
            if hasattr(message, 'voice'):
                file = await message.bot.get_file(message.voice.file_id)
            elif hasattr(message, 'audio'):
                file = await message.bot.get_file(message.audio.file_id)
            else:
                raise ValueError("Unsupported audio type")
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
                temp_path = temp_file.name
            
            # Скачиваем файл
            await message.bot.download_file(file.file_path, temp_path)
            
            # Получаем метаданные
            meta = self._get_audio_metadata(message)
            
            # Проверяем лимиты
            if meta['duration'] > self.max_duration:
                os.unlink(temp_path)
                raise ValueError(f"Audio too long: {meta['duration']}s > {self.max_duration}s")
            
            if meta['filesize_mb'] > self.max_size_mb:
                os.unlink(temp_path)
                raise ValueError(f"Audio too large: {meta['filesize_mb']}MB > {self.max_size_mb}MB")
            
            return temp_path, meta
            
        except Exception as e:
            logger.error(f"Error preparing audio: {e}")
            raise
    
    def _get_audio_metadata(self, message) -> Dict[str, Any]:
        """Получает метаданные аудиофайла"""
        if hasattr(message, 'voice'):
            return {
                'duration': message.voice.duration,
                'filesize_mb': message.voice.file_size / (1024 * 1024) if message.voice.file_size else 0,
                'mime_type': 'audio/ogg'
            }
        elif hasattr(message, 'audio'):
            return {
                'duration': message.audio.duration,
                'filesize_mb': message.audio.file_size / (1024 * 1024) if message.audio.file_size else 0,
                'mime_type': message.audio.mime_type
            }
        else:
            return {'duration': 0, 'filesize_mb': 0, 'mime_type': 'unknown'}
    
    async def transcribe(self, audio_path: str, lang_hint: str = "ru") -> tuple[str, str, float]:
        """
        Транскрибирует аудио в текст
        В минимальной реализации возвращает заглушку
        """
        try:
            # В реальной реализации здесь будет:
            # 1. Конвертация в WAV через ffmpeg
            # 2. Распознавание через faster-whisper или Vosk
            # 3. Определение языка
            
            # Заглушка для минимальной реализации
            logger.info(f"Transcribing audio: {audio_path}, lang: {lang_hint}")
            
            # Имитируем обработку
            await asyncio.sleep(1)
            
            # Возвращаем заглушку
            return "Привет, Карма! Сделай отчёт за неделю", "ru", 0.9
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return "", "ru", 0.0
        finally:
            # Удаляем временный файл
            try:
                os.unlink(audio_path)
            except:
                pass


# Импорт asyncio для заглушки
import asyncio
