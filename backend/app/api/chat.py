import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_db
from app.models.models import Conversation, Message
from app.models.schemas import ChatIn, ChatOut, ConversationOut
from app.services.retrieval import retrieve_top_chunks

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    convs = (
        await db.execute(
            select(Conversation).order_by(Conversation.created_at.desc())
        )
    ).scalars().all()

    return [
        ConversationOut(id=c.id, title=c.title, created_at=c.created_at)
        for c in convs
    ]


@router.post("", response_model=ChatOut)
async def chat(payload: ChatIn, db: AsyncSession = Depends(get_db)):
    # ✅ lazy imports (keep startup fast)
    from app.services.embeddings import embed_texts
    from app.services.llm import answer_query

    if payload.conversation_id is None:
        conv = Conversation(title="New conversation")
        db.add(conv)
        await db.flush()
        conversation_id = conv.id
    else:
        conversation_id = payload.conversation_id

    db.add(
        Message(
            conversation_id=conversation_id,
            role="user",
            content=payload.query,
        )
    )
    await db.commit()

    q_emb = (await embed_texts([payload.query]))[0]
    chunks = await retrieve_top_chunks(db, q_emb, payload.query)

    answer, citations = await answer_query(payload.query, chunks)

    db.add(
        Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            citations={"citations": citations},
        )
    )
    await db.commit()

    return ChatOut(
        conversation_id=conversation_id,
        answer=answer,
        citations=citations,
    )


@router.post("/stream")
async def chat_stream(payload: ChatIn, db: AsyncSession = Depends(get_db)):
    # ✅ lazy imports
    from app.services.embeddings import embed_texts
    from app.services.llm import stream_answer

    if payload.conversation_id is None:
        conv = Conversation(title="New conversation")
        db.add(conv)
        await db.flush()
        conversation_id = conv.id
    else:
        conversation_id = payload.conversation_id

    db.add(
        Message(
            conversation_id=conversation_id,
            role="user",
            content=payload.query,
        )
    )
    await db.commit()

    q_emb = (await embed_texts([payload.query]))[0]
    chunks = await retrieve_top_chunks(db, q_emb, payload.query)

    # ✅ CRITICAL FIX: make chunks JSON-safe
    safe_chunks = [
        {
            "chunk_id": c["chunk_id"],
            "document_id": c["document_id"],
            "chunk_index": c["chunk_index"],
            "score": float(c["score"]) if c["score"] is not None else None,
            "title": c.get("title"),
            "text": c.get("text"),
        }
        for c in chunks
    ]

    async def event_gen():
        # meta event (SAFE JSON)
        yield (
            "event: meta\n"
            f"data: {json.dumps({'conversation_id': conversation_id, 'citations': safe_chunks})}\n\n"
        )

        buf = []
        async for token in stream_answer(payload.query, chunks):
            buf.append(token)
            yield f"data: {token}\n\n"

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

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
    )