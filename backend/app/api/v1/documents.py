from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, audit
from app.models import Document
from app.models.enums import DocumentStatus, DocumentType
from app.schemas.documents import DocumentOut
from app.services.document_parser import parse_document
from app.services.storage import save_upload

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
) -> Document:
    try:
        path, size, checksum = await save_upload(file, "uploads")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    page_count = None
    extracted = None
    try:
        parsed = parse_document(path, file.content_type)
        page_count = parsed.page_count
        extracted = parsed.text
    except Exception:
        # Keep upload; analysis will retry parse
        pass

    doc = Document(
        owner_id=user.id,
        filename=path.name,
        original_filename=file.filename or path.name,
        content_type=file.content_type or "application/octet-stream",
        file_size=size,
        storage_path=str(path),
        document_type=document_type.value,
        status=DocumentStatus.UPLOADED.value,
        page_count=page_count,
        checksum_sha256=checksum,
        extracted_text=extracted,
    )
    db.add(doc)
    await db.flush()
    await audit(request, db, user, "document.upload", "document", str(doc.id), {"filename": doc.original_filename})
    return doc


@router.get("", response_model=list[DocumentOut])
async def list_documents(db: DbSession, user: CurrentUser) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.owner_id == user.id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: UUID, db: DbSession, user: CurrentUser) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, request: Request, db: DbSession, user: CurrentUser) -> None:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    Path(doc.storage_path).unlink(missing_ok=True)
    await db.delete(doc)
    await audit(request, db, user, "document.delete", "document", str(document_id))
