import os
import uuid
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.api.dependencies import get_db
from app.models.models import (
    Document,
    IngestionJob,
    SourceType,
    DocumentStatus,
    JobStatus,
    JobStage,
)
from app.models.schemas import (
    IngestTextIn,
    IngestUrlIn,
    DocumentOut,
    JobOut,
)
from app.services.ingestion.pipeline import run_ingestion_pipeline

router = APIRouter()


# --------------------------------------------------
# SAFE ORM → SCHEMA CONVERTER (CRITICAL FIX)
# --------------------------------------------------
def _doc_out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        source_uri=doc.source_uri,
        mime_type=doc.mime_type,
        size_bytes=doc.size_bytes,
        status=doc.status,
        error=doc.error,
        created_at=doc.created_at,
        ingested_at=doc.ingested_at,
        source_published_at=doc.source_published_at,
    )


# --------------------------------------------------
# TEXT INGEST
# --------------------------------------------------
@router.post("/text", response_model=DocumentOut)
async def ingest_text(
    payload: IngestTextIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    doc = Document(
        title=payload.title,
        source_type=SourceType.text,
        source_uri=None,
        mime_type="text/plain",
        size_bytes=len(payload.text.encode("utf-8", errors="ignore")),
        status=DocumentStatus.processing,
        created_at=datetime.utcnow(),
    )
    db.add(doc)
    await db.flush()

    job = IngestionJob(
        document_id=doc.id,
        status=JobStatus.queued,
        stage=JobStage.extract,
    )
    db.add(job)
    await db.commit()

    background_tasks.add_task(
        run_ingestion_pipeline,
        db,
        doc.id,
        source_type=SourceType.text,
        text_input=payload.text,
    )

    return _doc_out(doc)


# --------------------------------------------------
# URL INGEST (FIXED ENUM + size_bytes)
# --------------------------------------------------
@router.post("/url", response_model=DocumentOut)
async def ingest_url(
    payload: IngestUrlIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    doc = Document(
        title=payload.title or payload.url,
        source_type=SourceType.url,        # ✅ MUST MATCH ENUM
        source_uri=payload.url,
        mime_type="text/html",
        size_bytes=None,                   # ✅ REQUIRED for Pydantic
        status=DocumentStatus.processing,
        created_at=datetime.utcnow(),
    )
    db.add(doc)
    await db.flush()

    job = IngestionJob(
        document_id=doc.id,
        status=JobStatus.queued,
        stage=JobStage.extract,
    )
    db.add(job)
    await db.commit()

    background_tasks.add_task(
        run_ingestion_pipeline,
        db,
        doc.id,
        source_type=SourceType.url,
        url=payload.url,
    )

    return _doc_out(doc)


# --------------------------------------------------
# FILE INGEST
# --------------------------------------------------
@router.post("/file", response_model=DocumentOut)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    os.makedirs(settings.upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    fname = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.upload_dir, fname)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty upload")

    with open(path, "wb") as f:
        f.write(content)

    doc = Document(
        title=file.filename,
        source_type=SourceType.document,
        source_uri=path,
        mime_type=file.content_type,
        size_bytes=len(content),
        status=DocumentStatus.processing,
        created_at=datetime.utcnow(),
    )
    db.add(doc)
    await db.flush()

    job = IngestionJob(
        document_id=doc.id,
        status=JobStatus.queued,
        stage=JobStage.extract,
    )
    db.add(job)
    await db.commit()

    background_tasks.add_task(
        run_ingestion_pipeline,
        db,
        doc.id,
        source_type=SourceType.document,
        file_path=path,
    )

    return _doc_out(doc)

# --------------------------------------------------
# AUDIO INGEST 
# --------------------------------------------------
@router.post("/audio", response_model=DocumentOut)
async def ingest_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid audio file")

    os.makedirs(settings.upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1].lower() or ".wav"
    fname = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.upload_dir, fname)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty upload")

    with open(path, "wb") as f:
        f.write(content)

    doc = Document(
        title=file.filename,
        source_type=SourceType.audio,   # ✅ enum already exists
        source_uri=path,
        mime_type=file.content_type,
        size_bytes=len(content),
        status=DocumentStatus.processing,
        created_at=datetime.utcnow(),
    )
    db.add(doc)
    await db.flush()

    job = IngestionJob(
        document_id=doc.id,
        status=JobStatus.queued,
        stage=JobStage.extract,
    )
    db.add(job)
    await db.commit()

    background_tasks.add_task(
        run_ingestion_pipeline,
        db,
        doc.id,
        source_type=SourceType.audio,
        file_path=path,
    )

    return _doc_out(doc)
# --------------------------------------------------
# JOB STATUS
# --------------------------------------------------
@router.get("/jobs/{document_id}", response_model=JobOut)
async def job_status(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    job = (
        await db.execute(
            select(IngestionJob).where(IngestionJob.document_id == document_id)
        )
    ).scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobOut(
        document_id=document_id,
        status=job.status.value,
        stage=job.stage.value,
        error=job.error,
    )