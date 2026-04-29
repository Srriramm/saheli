import os
import io
import wave
import json
import logging
import subprocess
import tempfile
from typing import Optional
from pathlib import Path

# Try importing whisper, handle missing nicely
try:
    import whisper
except ImportError:
    logging.error("whisper not found. Run pip install openai-whisper")
    whisper = None

try:
    import torch
except ImportError:
    torch = None

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

from config.settings import WHISPER_MODEL, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

TAMIL_WHISPER_MODEL = "vasista22/whisper-tamil-small"


class WhisperRunner:
    """Offline multilingual speech-to-text with a Tamil-specialized demo path."""

    def __init__(self, model_size: str = WHISPER_MODEL):
        self.model_size = model_size
        self.model = None
        self.tamil_asr = None

    def _ffmpeg_executable(self) -> Optional[str]:
        """Return system ffmpeg or the imageio-ffmpeg bundled binary."""
        if imageio_ffmpeg:
            try:
                return imageio_ffmpeg.get_ffmpeg_exe()
            except Exception as e:
                logging.warning(f"imageio-ffmpeg unavailable: {e}")
        return "ffmpeg"

    def _prepare_audio_for_asr(self, audio_path: str) -> tuple[str, bool]:
        """
        Convert browser WebM/other compressed audio to 16 kHz mono WAV.
        Transformers and Whisper both depend on ffmpeg-style decoding; on Windows,
        the browser upload fails unless ffmpeg is available somewhere.
        """
        suffix = Path(audio_path).suffix.lower()
        if suffix == ".wav":
            return audio_path, False

        ffmpeg_exe = self._ffmpeg_executable()
        if not ffmpeg_exe:
            return audio_path, False

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_path = tmp.name
        tmp.close()

        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            audio_path,
            "-ac",
            "1",
            "-ar",
            "16000",
            "-loglevel",
            "error",
            tmp_path,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return tmp_path, True
        except Exception as e:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            logging.warning(f"Audio conversion failed, trying original file: {e}")
            return audio_path, False

    def _load_openai_whisper(self) -> bool:
        """Load generic Whisper on CPU so Gemma keeps the GPU."""
        if self.model:
            return True
        if not whisper:
            return False
        logging.info(f"Loading Whisper model ({self.model_size}) on CPU")
        self.model = whisper.load_model(self.model_size, device="cpu")
        logging.info("Whisper model loaded successfully.")
        return True

    def _load_tamil_asr(self) -> bool:
        """Load the Tamil fine-tuned Hugging Face Whisper pipeline lazily."""
        if self.tamil_asr:
            return True
        if not pipeline:
            logging.warning("transformers not installed; falling back to generic Whisper for Tamil ASR.")
            return False

        device = 0 if torch is not None and torch.cuda.is_available() else -1
        logging.info(
            "Loading Tamil ASR model %s on %s",
            TAMIL_WHISPER_MODEL,
            "CUDA" if device == 0 else "CPU",
        )
        try:
            self.tamil_asr = pipeline(
                task="automatic-speech-recognition",
                model=TAMIL_WHISPER_MODEL,
                chunk_length_s=30,
                device=device,
            )
            logging.info("Tamil ASR model loaded successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to load Tamil ASR model: {e}")
            return False

    @staticmethod
    def _ensure_ffmpeg_in_path():
        """
        openai-whisper and transformers both call subprocess(["ffmpeg", ...]).
        imageio-ffmpeg ships the binary as ffmpeg-win-x86_64-v7.1.exe (versioned name),
        so adding its directory to PATH is not enough on Windows.
        We copy it once as ffmpeg.exe into a temp dir and add that to PATH.
        """
        if not imageio_ffmpeg:
            return
        if getattr(WhisperRunner, '_ffmpeg_dir_patched', False):
            return
        try:
            import shutil, tempfile
            src = imageio_ffmpeg.get_ffmpeg_exe()
            tmp_dir = tempfile.mkdtemp(prefix='saheli_ffmpeg_')
            shutil.copy(src, os.path.join(tmp_dir, 'ffmpeg.exe'))
            os.environ['PATH'] = tmp_dir + os.pathsep + os.environ.get('PATH', '')
            WhisperRunner._ffmpeg_dir_patched = True
        except Exception as e:
            logging.warning(f"ffmpeg PATH setup failed: {e}")

    def transcribe_file(self, audio_path: str, language: Optional[str] = None) -> str:
        """Transcribe an existing file. Auto-detects language if none provided."""
        WhisperRunner._ensure_ffmpeg_in_path()
        prepared_path, should_cleanup = self._prepare_audio_for_asr(audio_path)

        try:
            if language == "ta" and self._load_tamil_asr():
                try:
                    result = self.tamil_asr(
                        prepared_path,
                        generate_kwargs={"language": "ta", "task": "transcribe"},
                    )
                    text = result.get("text", "").strip() if isinstance(result, dict) else str(result).strip()
                    if text:
                        return text
                    logging.warning("Tamil ASR returned empty text, falling back to generic Whisper.")
                except Exception as e:
                    logging.warning(f"Tamil ASR inference failed, falling back to generic Whisper: {e}")

            if not self._load_openai_whisper():
                return ""

            options = {"fp16": False, "language": language} if language else {"fp16": False}
            result = self.model.transcribe(prepared_path, **options)
            return result["text"].strip()
        finally:
            if should_cleanup:
                try:
                    os.remove(prepared_path)
                except OSError:
                    pass

    def transcribe_microphone(self, duration_seconds: int = 10, language: Optional[str] = None) -> str:
        """Capture audio from mic and transcribe. Requires audio helper module."""
        from audio.recorder import record_audio

        audio_file = record_audio(duration=duration_seconds, sample_rate=16000)
        
        if not audio_file or not os.path.exists(audio_file):
            return ""
            
        transcription = self.transcribe_file(audio_file, language=language)
        
        # Cleanup
        try:
            os.remove(audio_file)
        except OSError:
            pass
            
        return transcription

    def get_detected_language(self, audio_path: str) -> str:
        """Return the auto-detected ISO language code (e.g. 'kn', 'hi', 'te')"""
        if not self.model:
            return DEFAULT_LANGUAGE

        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)

        # Make log-Mel spectrogram
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

        # Detect the language
        _, probs = self.model.detect_language(mel)
        lang_code = max(probs, key=probs.get)
        
        if lang_code in ['hi', 'te', 'ta']:
            return lang_code
            
        return "kn" if lang_code not in SUPPORTED_LANGUAGES else lang_code
