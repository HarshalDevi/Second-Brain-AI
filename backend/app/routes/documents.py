from fastapi import APIRouter

router = APIRouter()

@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    return {"id": document_id, "status": "active"}
