from fastapi import APIRouter

from app.api.ingest import router as ingest_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router

router = APIRouter()
router.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(documents_router, prefix="/documents", tags=["documents"])