import os
import uuid
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_workspace_id
from app.config import settings

from app.models.models import (
    Document,
    DocumentStatus,
    IngestionJob,
    JobStage,
    JobStatus,
    SourceType,
)
from app.models.schemas import DocumentOut, IngestTextIn, IngestUrlIn, JobOut
from app.services.ingestion.documents import supported_document_extensions
from app.services.ingestion.pipeline import run_ingestion_pipeline

router = APIRouter()


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
        workspace_id=doc.workspace_id,
    )


async def _create_job(db: AsyncSession, doc_id: int) -> None:
    db.add(
        IngestionJob(
            document_id=doc_id,
            status=JobStatus.queued,
            stage=JobStage.extract,
        )
    )
    await db.commit()


@router.post("/text", response_model=DocumentOut)
async def ingest_text(
    payload: IngestTextIn,
    background_tasks: BackgroundTasks,
    workspace_id: str = Depends(get_workspace_id),
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
        workspace_id=workspace_id,
    )
    db.add(doc)
    await db.flush()
    await _create_job(db, doc.id)

    background_tasks.add_task(
        run_ingestion_pipeline,
        doc.id,
        source_type=SourceType.text,
        text_input=payload.text,
    )

    return _doc_out(doc)


@router.post("/url", response_model=DocumentOut)
async def ingest_url(
    payload: IngestUrlIn,
    background_tasks: BackgroundTasks,
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    doc = Document(
        title=payload.title or payload.url,
        source_type=SourceType.url,
        source_uri=payload.url,
        mime_type="text/html",
        size_bytes=None,
        status=DocumentStatus.processing,
        created_at=datetime.utcnow(),
        workspace_id=workspace_id,
    )
    db.add(doc)
    await db.flush()
    await _create_job(db, doc.id)

    background_tasks.add_task(
        run_ingestion_pipeline,
        doc.id,
        source_type=SourceType.url,
        url=payload.url,
    )

    return _doc_out(doc)


@router.post("/file", response_model=DocumentOut)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    os.makedirs(settings.upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    if ext not in supported_document_extensions():
        supported = ", ".join(sorted(supported_document_extensions()))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported document type '{ext}'. Supported types: {supported}",
        )

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
        workspace_id=workspace_id,
    )
    db.add(doc)
    await db.flush()
    await _create_job(db, doc.id)

    background_tasks.add_task(
        run_ingestion_pipeline,
        doc.id,
        source_type=SourceType.document,
        file_path=path,
    )

    return _doc_out(doc)


@router.post("/audio", response_model=DocumentOut)
async def ingest_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("audio/"):
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
        source_type=SourceType.audio,
        source_uri=path,
        mime_type=file.content_type,
        size_bytes=len(content),
        status=DocumentStatus.processing,
        created_at=datetime.utcnow(),
        workspace_id=workspace_id,
    )
    db.add(doc)
    await db.flush()
    await _create_job(db, doc.id)

    background_tasks.add_task(
        run_ingestion_pipeline,
        doc.id,
        source_type=SourceType.audio,
        file_path=path,
    )

    return _doc_out(doc)


@router.get("/jobs/{document_id}", response_model=JobOut)
async def job_status(
    document_id: int,
    workspace_id: str = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    job = (
        await db.execute(
            select(IngestionJob)
            .join(Document)
            .where(
                IngestionJob.document_id == document_id,
                Document.workspace_id == workspace_id,
            )
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