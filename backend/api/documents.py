import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db, DocumentRecord
from backend.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg", ".tiff"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    task_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    doc_id = str(uuid.uuid4())
    dest_path = settings.DOCUMENTS_DIR / f"{doc_id}{ext}"

    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    record = DocumentRecord(
        id=doc_id,
        filename=file.filename,
        file_path=str(dest_path),
        file_type=ext,
        task_id=task_id,
        status="uploaded",
    )
    db.add(record)
    await db.commit()

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "file_type": ext,
        "file_path": str(dest_path),
        "status": "uploaded",
    }


@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentRecord).order_by(DocumentRecord.created_at.desc()))
    docs = result.scalars().all()
    return [
        {
            "doc_id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "task_id": d.task_id,
            "status": d.status,
            "created_at": str(d.created_at),
        }
        for d in docs
    ]


@router.get("/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "doc_id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_path": doc.file_path,
        "task_id": doc.task_id,
        "extracted_text": doc.extracted_text,
        "status": doc.status,
        "created_at": str(doc.created_at),
    }


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink()
    await db.delete(doc)
    await db.commit()
    return {"status": "deleted", "doc_id": doc_id}
