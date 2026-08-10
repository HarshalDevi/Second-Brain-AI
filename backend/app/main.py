import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import engine, Base
from app.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)

    async with engine.begin() as conn:
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.run_sync(Base.metadata.create_all)
        await conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN IF NOT EXISTS workspace_id VARCHAR(120);")
        await conn.exec_driver_sql("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS workspace_id VARCHAR(120);")
        await conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_documents_workspace_id ON documents (workspace_id);")
        await conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_conversations_workspace_id ON conversations (workspace_id);")

    yield

    await engine.dispose()


app = FastAPI(title="SecondBrain", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"service": "SecondBrain", "status": "running"}
