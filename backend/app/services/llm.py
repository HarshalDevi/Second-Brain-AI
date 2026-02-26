from openai import AsyncOpenAI
from app.config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)


def build_context_snippets(chunks: list[dict], max_chars: int = 8000) -> str:
    parts = []
    total = 0
    for c in chunks:
        header = f"[doc:{c['document_id']} chunk:{c['chunk_index']} score:{c['score']:.3f} title:{c.get('doc_title') or ''}]"
        body = c["text"].strip()
        block = header + "\n" + body
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n---\n\n".join(parts)


async def answer_query(query: str, chunks: list[dict]) -> tuple[str, list[dict]]:
    context = build_context_snippets(chunks)
    sys = (
        "You are a helpful Second Brain assistant. "
        "Answer using ONLY the provided context when possible. "
        "If the context is insufficient, say what is missing."
    )

    user = f"Context:\n{context}\n\nUser question:\n{query}"

    resp = await _client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    answer = resp.choices[0].message.content or ""

    citations = []
    for c in chunks:
        citations.append(
            {
                "chunk_id": c["chunk_id"],
                "document_id": c["document_id"],
                "chunk_index": c["chunk_index"],
                "score": c["score"],
                "title": c.get("doc_title"),
            }
        )
    return answer, citations


async def stream_answer(query: str, chunks: list[dict]):
    context = build_context_snippets(chunks)
    sys = (
        "You are a helpful Second Brain assistant. "
        "Answer using ONLY the provided context when possible. "
        "If insufficient, say what is missing."
    )
    user = f"Context:\n{context}\n\nUser question:\n{query}"

    stream = await _client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        stream=True,
    )

    async for event in stream:
        if not event.choices:
            continue
        delta = event.choices[0].delta
        if delta and delta.content:
            yield delta.content