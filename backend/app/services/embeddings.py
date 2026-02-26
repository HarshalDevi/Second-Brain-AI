from openai import AsyncOpenAI
from app.config import settings


_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Batch embeddings.
    """
    if not texts:
        return []
    resp = await _client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [d.embedding for d in resp.data]