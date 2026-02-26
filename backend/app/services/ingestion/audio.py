from openai import AsyncOpenAI
from app.config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def transcribe_audio(file_path: str) -> str:
    """
    Uses OpenAI Whisper API.
    """
    with open(file_path, "rb") as f:
        resp = await _client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )
    return (resp.text or "").strip()