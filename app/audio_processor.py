"""Audio and video transcription module for ReQperacion.

Uses OpenAI Whisper to transcribe speech from audio files and
audio tracks extracted from video files.

Supported formats:
- Audio: MP3, WAV, FLAC, OGG, M4A, AAC, WMA
- Video: MP4, AVI, MOV, MKV, WEBM, FLV
"""

import os
import subprocess
import logging
import tempfile

logger = logging.getLogger(__name__)

# Audio file extensions
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"}

# Video file extensions
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".mpeg", ".mpg"}


def is_audio_file(filename: str) -> bool:
    """Check if a file is a supported audio format."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in AUDIO_EXTENSIONS


def is_video_file(filename: str) -> bool:
    """Check if a file is a supported video format."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in VIDEO_EXTENSIONS


def extract_audio_from_video(video_path: str) -> str | None:
    """
    Extract audio track from a video file using ffmpeg.
    Returns the path to a temporary WAV file, or None on failure.
    """
    try:
        # Create a temporary file for the audio output
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()

        # Use ffmpeg to extract audio
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",                    # No video
            "-acodec", "pcm_s16le",   # PCM 16-bit WAV
            "-ar", "16000",           # 16kHz sample rate (optimal for Whisper)
            "-ac", "1",               # Mono
            "-y",                     # Overwrite output
            temp_audio_path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for long videos
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg error: {result.stderr}")
            os.unlink(temp_audio_path)
            return None

        logger.info(f"Audio extracted from video to {temp_audio_path}")
        return temp_audio_path

    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timed out extracting audio from video")
        return None
    except FileNotFoundError:
        logger.error("ffmpeg is not installed. Install it with: apt-get install ffmpeg")
        return None
    except Exception as e:
        logger.error(f"Error extracting audio from video: {e}")
        return None


def transcribe_audio(audio_path: str, language: str = "es") -> str:
    """
    Transcribe an audio file using OpenAI Whisper.
    
    Args:
        audio_path: Path to the audio file (WAV, MP3, etc.)
        language: Language code (e.g., "es" for Spanish, "en" for English)
                 "es" by default since the user is Spanish-speaking
    
    Returns:
        Transcribed text string, or empty string on failure
    """
    if not os.path.exists(audio_path):
        logger.warning(f"Audio file not found: {audio_path}")
        return ""

    try:
        import whisper

        # Load the model (will be cached after first use)
        # "tiny" is the smallest model (~75MB, fast on CPU)
        # "base" is slightly larger (~150MB, better accuracy)
        # "small" is ~500MB, even better
        logger.info("Loading Whisper model (tiny)...")
        model = whisper.load_model("tiny")

        # Transcribe
        logger.info(f"Transcribing audio: {audio_path}")
        result = model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            fp16=False,  # Use FP32 on CPU
        )

        text = result.get("text", "").strip()
        logger.info(
            f"Transcription complete: {len(text)} characters"
        )
        return text

    except ImportError:
        logger.error(
            "openai-whisper is not installed. "
            "Run: pip install openai-whisper"
        )
        return ""
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""


def process_audio(file_path: str) -> str:
    """
    Process an audio file and return transcribed text.
    """
    return transcribe_audio(file_path)


def process_video(file_path: str) -> str:
    """
    Process a video file: extract audio, then transcribe.
    Returns transcribed text, or empty string on failure.
    """
    # Extract audio from video
    temp_audio_path = extract_audio_from_video(file_path)
    if not temp_audio_path:
        return ""

    try:
        # Transcribe the extracted audio
        text = transcribe_audio(temp_audio_path)
        return text
    finally:
        # Clean up temporary audio file
        try:
            os.unlink(temp_audio_path)
        except OSError:
            pass
