import json
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_workspace_id
from app.models.models import Conversation, Message
from app.models.schemas import ChatIn, ChatOut, ConversationOut
from app.services.retrieval import retrieve_top_chunks

router = APIRouter()

NO_RELEVANT_CONTEXT_MESSAGE = (
    "I could not find relevant information in your ingested sources for that question. "
    "Try adding a more specific document or rephrasing the question."
)

SMALL_TALK_RESPONSES = {
    "hi": "Hello! How can I help you with your second brain today?",
    "hello": "Hello! How can I help you with your second brain today?",
    "hey": "Hey! Ask me anything about your ingested knowledge base.",
    "thanks": "You're welcome.",
    "thank you": "You're welcome.",
}


def small_talk_response(query: str) -> str | None:
    normalized = " ".join(query.lower().strip().strip(".!?").split())
    if normalized in SMALL_TALK_RESPONSES:
        return SMALL_TALK_RESPONSES[normalized]
    if normalized in {"good morning", "good afternoon", "good evening"}:
        return "Hello! What would you like to explore from your knowledge base?"
    if re.fullmatch(r"(hi|hello|hey|yo|hiya)[, ]+(how are you|how r u|how are u)\??", normalized):
        return "I'm doing well and ready to help. Ask me anything from your second brain."
    if re.fullmatch(r"(how are you|how r u|how are u)\??", normalized):
        return "I'm doing well and ready to help. What would you like to explore?"
    if re.fullmatch(r"(hi|hello|hey|yo|hiya)\b.*", normalized) and len(normalized.split()) <= 5:
        return "Hello! How can I help you with your second brain today?"
    return None


def citation_payload(chunks: list[dict]) -> list[dict]:
    return [
        {
            "chunk_id": c["chunk_id"],
            "document_id": c["document_id"],
            "chunk_index": c["chunk_index"],
            "score": float(c["score"]) if c["score"] is not None else None,
            "title": c.get("doc_title"),
            "text": c.get("text"),
        }
        for c in chunks
    ]


async def get_or_create_conversation(
    db: AsyncSession,
    conversation_id: int | None,
    workspace_id: str,
) -> int:
    if conversation_id is None:
        conv = Conversation(title="New conversation", workspace_id=workspace_id)
        db.add(conv)
        await db.flush()
        return conv.id

    existing = (
        await db.execute(
            select(Conversation.id).where(
                Conversation.id == conversation_id,
                Conversation.workspace_id == workspace_id,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return existing


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    convs = (
        await db.execute(
            select(Conversation)
            .where(Conversation.workspace_id == workspace_id)
            .order_by(Conversation.created_at.desc())
        )
    ).scalars().all()

    return [
        ConversationOut(id=c.id, title=c.title, created_at=c.created_at)
        for c in convs
    ]


@router.post("", response_model=ChatOut)
async def chat(
    payload: ChatIn,
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    from app.services.embeddings import embed_texts
    from app.services.llm import answer_query

    conversation_id = await get_or_create_conversation(
        db,
        payload.conversation_id,
        workspace_id,
    )

    db.add(Message(conversation_id=conversation_id, role="user", content=payload.query))
    await db.commit()

    answer = small_talk_response(payload.query)
    citations = []
    if answer is None:
        q_emb = (await embed_texts([payload.query]))[0]
        chunks = await retrieve_top_chunks(db, q_emb, payload.query, workspace_id)
        if chunks:
            answer, citations = await answer_query(payload.query, chunks)
        else:
            answer = NO_RELEVANT_CONTEXT_MESSAGE

    db.add(
        Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            citations={"citations": citations},
        )
    )
    await db.commit()

    return ChatOut(conversation_id=conversation_id, answer=answer, citations=citations)


@router.post("/stream")
async def chat_stream(
    payload: ChatIn,
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    from app.services.embeddings import embed_texts
    from app.services.llm import stream_answer

    conversation_id = await get_or_create_conversation(
        db,
        payload.conversation_id,
        workspace_id,
    )

    db.add(Message(conversation_id=conversation_id, role="user", content=payload.query))
    await db.commit()

    small_talk_answer = small_talk_response(payload.query)
    chunks = []
    if small_talk_answer is None:
        q_emb = (await embed_texts([payload.query]))[0]
        chunks = await retrieve_top_chunks(db, q_emb, payload.query, workspace_id)

    safe_chunks = citation_payload(chunks)

    async def event_gen():
        yield (
            "event: meta\n"
            f"data: {json.dumps({'conversation_id': conversation_id, 'citations': safe_chunks})}\n\n"
        )

        buf = []
        if small_talk_answer is not None:
            buf.append(small_talk_answer)
            yield f"data: {json.dumps({'token': small_talk_answer})}\n\n"
        elif not chunks:
            buf.append(NO_RELEVANT_CONTEXT_MESSAGE)
            yield f"data: {json.dumps({'token': NO_RELEVANT_CONTEXT_MESSAGE})}\n\n"
        else:
            async for token in stream_answer(payload.query, chunks):
                buf.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

        final_text = "".join(buf)
        yield "event: done\ndata: {}\n\n"

        db.add(
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_text,
                citations={"citations": safe_chunks},
            )
        )
        await db.commit()

    return StreamingResponse(event_gen(), media_type="text/event-stream")

