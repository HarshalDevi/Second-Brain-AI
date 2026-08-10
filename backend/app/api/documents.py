from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_workspace_id
from app.models.models import Chunk, Document
from app.models.schemas import ChunkOut, DocumentOut

router = APIRouter()


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    docs = (
        await db.execute(
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc())
        )
    ).scalars().all()
    return [DocumentOut(**d.__dict__) for d in docs]


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: int,
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    doc = (
        await db.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.workspace_id == workspace_id,
            )
        )
    ).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentOut(**doc.__dict__)


@router.get("/{doc_id}/chunks", response_model=list[ChunkOut])
async def get_document_chunks(
    doc_id: int,
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    doc = (
        await db.execute(
            select(Document.id).where(
                Document.id == doc_id,
                Document.workspace_id == workspace_id,
            )
        )
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = (
        await db.execute(
            select(Chunk)
            .where(Chunk.document_id == doc_id)
            .order_by(Chunk.chunk_index.asc())
        )
    ).scalars().all()

    return [
        ChunkOut(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            text=c.text,
            created_at=c.created_at,
        )
        for c in chunks
    ]


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    doc = (
        await db.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.workspace_id == workspace_id,
            )
        )
    ).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.execute(delete(Document).where(Document.id == doc_id))
    await db.commit()

    return {"deleted": True, "document_id": doc_id}