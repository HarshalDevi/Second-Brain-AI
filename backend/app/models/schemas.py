from datetime import datetime
from pydantic import BaseModel, Field


class IngestTextIn(BaseModel):
    title: str | None = None
    text: str

class IngestUrlIn(BaseModel):
    title: str | None = None
    url: str

class DocumentOut(BaseModel):
    id: int
    title: str | None
    source_type: str
    source_uri: str | None
    mime_type: str | None
    size_bytes: int | None
    status: str
    created_at: datetime | None

class JobOut(BaseModel):
    document_id: int
    status: str
    stage: str
    error: str | None


class ChatIn(BaseModel):
    query: str = Field(min_length=1)
    conversation_id: int | None = None


class ChatOut(BaseModel):
    conversation_id: int
    answer: str
    citations: list[dict] = []


class ConversationOut(BaseModel):
    id: int
    title: str | None
    created_at: datetime


class ChunkOut(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    text: str
    created_at: datetime