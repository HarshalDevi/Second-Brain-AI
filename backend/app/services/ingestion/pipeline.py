from datetime import datetime
from sqlalchemy import update, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.models import (
    Document,
    Chunk,
    ChunkEmbedding,
    DocumentStatus,
    JobStatus,
    JobStage,
    SourceType,
    IngestionJob,
)
from app.services.chunking import chunk_text
from app.services.embeddings import embed_texts
from app.services.ingestion.documents import extract_text_from_file
from app.services.ingestion.web import fetch_and_extract_url
from app.services.ingestion.audio import transcribe_audio


async def _set_job(
    db: AsyncSession,
    doc_id: int,
    status: JobStatus,
    stage: JobStage,
    error: str | None = None,
):
    await db.execute(
        update(IngestionJob)
        .where(IngestionJob.document_id == doc_id)
        .values(
            status=status,
            stage=stage,
            error=error,
            updated_at=datetime.utcnow(),
        )
    )


async def _set_doc_status(
    db: AsyncSession,
    doc_id: int,
    status: DocumentStatus,
    error: str | None = None,
):
    await db.execute(
        update(Document)
        .where(Document.id == doc_id)
        .values(status=status, error=error)
    )


# ✅ FIXED: db is created INSIDE
async def run_ingestion_pipeline(
    document_id: int,
    *,
    source_type: SourceType,
    text_input: str | None = None,
    file_path: str | None = None,
    url: str | None = None,
):
    async with AsyncSessionLocal() as db:
        try:
            # ---- extract ----
            await _set_job(db, document_id, JobStatus.processing, JobStage.extract)
            await db.commit()

            raw_text = ""
            derived_title = None

            if source_type == SourceType.text:
                raw_text = (text_input or "").strip()

            elif source_type == SourceType.document:
                if not file_path:
                    raise ValueError("file_path is required for document ingestion")
                raw_text = extract_text_from_file(file_path)

            elif source_type == SourceType.url:
                if not url:
                    raise ValueError("url is required for url ingestion")
                derived_title, raw_text = await fetch_and_extract_url(url)

            elif source_type == SourceType.audio:
                if not file_path:
                    raise ValueError("file_path is required for audio ingestion")
                raw_text = await transcribe_audio(file_path)

            else:
                raise ValueError(f"Unsupported source_type: {source_type}")

            if not raw_text.strip():
                raise ValueError("No text extracted")

            if derived_title:
                await db.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .values(title=derived_title)
                )
                await db.commit()

            # ---- chunk ----
            await _set_job(db, document_id, JobStatus.processing, JobStage.chunk)
            await db.commit()

            chunks = chunk_text(raw_text)
            if not chunks:
                raise ValueError("Chunking produced 0 chunks")

            # ---- embed ----
            await _set_job(db, document_id, JobStatus.processing, JobStage.embed)
            await db.commit()

            embeddings = await embed_texts([c.text for c in chunks])

            # ---- store ----
            await _set_job(db, document_id, JobStatus.processing, JobStage.store)
            await db.commit()

            for c, emb in zip(chunks, embeddings):
                chunk_row = Chunk(
                    document_id=document_id,
                    chunk_index=c.index,
                    text=c.text,
                    token_count=c.token_count,
                )
                db.add(chunk_row)
                await db.flush()

                db.add(
                    ChunkEmbedding(
                        chunk_id=chunk_row.id,
                        embedding=emb,
                    )
                )

                await db.execute(
                    text("UPDATE chunks SET tsv = :t WHERE id = :id"),
                    {"t": c.text, "id": chunk_row.id},
                )

            # ---- complete ----
            await _set_job(db, document_id, JobStatus.done, JobStage.complete)
            await _set_doc_status(db, document_id, DocumentStatus.ready, None)
            await db.commit()

        except Exception as e:
            await _set_job(db, document_id, JobStatus.failed, JobStage.complete, str(e))
            await _set_doc_status(db, document_id, DocumentStatus.error, str(e))
            await db.commit()
            raise