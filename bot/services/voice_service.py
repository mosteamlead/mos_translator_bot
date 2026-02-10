import os
import tempfile
from pathlib import Path

from pydub import AudioSegment

from bot.config import settings
from bot.services.openai_client import client


async def convert_ogg_to_mp3(input_path: Path) -> Path:
    """
    Convert OGG/OPUS file to MP3 using pydub (requires ffmpeg installed).
    Returns path to MP3 file.
    """
    audio = AudioSegment.from_file(input_path)
    tmp_dir = Path(tempfile.gettempdir())
    output_path = tmp_dir / (input_path.stem + ".mp3")
    audio.export(output_path, format="mp3")
    return output_path


async def transcribe_audio(input_path: Path) -> str:
    """
    Transcribe audio file using Whisper (OpenAI).
    Accepts OGG/MP3/etc; converts if needed.
    Returns recognized text.
    """
    path = Path(input_path)

    if path.suffix.lower() != ".mp3":
        path = await convert_ogg_to_mp3(path)

    with path.open("rb") as audio_file:
        response = await client.audio.transcriptions.create(
            model=settings.openai_whisper_model,
            file=audio_file,
            response_format="text",
        )

    try:
        if path.exists() and path.suffix.lower() == ".mp3":
            os.remove(path)
    except OSError:
        pass

    return response.strip()