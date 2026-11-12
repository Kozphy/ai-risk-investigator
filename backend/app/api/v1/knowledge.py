from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, audit, require_role
from app.core.security import Role
from app.models import KnowledgeDocument, User
from app.models.enums import KnowledgeSourceType
from app.rag.store import RAGStore
from app.schemas.documents import KnowledgeOut
from app.services.document_parser import chunk_text, parse_document
from app.services.storage import save_upload

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
async def upload_knowledge(
    request: Request,
    db: DbSession,
    user: Annotated[User, Depends(require_role(Role.COMPLIANCE))],
    file: UploadFile = File(...),
    title: str = Form(...),
    source_type: KnowledgeSourceType = Form(KnowledgeSourceType.REGULATION),
    framework: str | None = Form(None),
) -> KnowledgeDocument:
    try:
        path, _, _ = await save_upload(file, "knowledge")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    kd = KnowledgeDocument(
        title=title,
        source_type=source_type.value,
        framework=framework,
        filename=file.filename or path.name,
        storage_path=str(path),
        uploaded_by=user.id,
    )
    db.add(kd)
    await db.flush()

    parsed = parse_document(Path(path), file.content_type)
    chunks = [(i, c, framework) for i, c in enumerate(chunk_text(parsed.text))]
    store = RAGStore(db)
    await store.upsert_knowledge_embeddings(kd.id, chunks)
    await audit(
        request, db, user, "knowledge.upload", "knowledge_document", str(kd.id), {"framework": framework}
    )
    return kd


@router.get("", response_model=list[KnowledgeOut])
async def list_knowledge(db: DbSession, user: CurrentUser) -> list[KnowledgeDocument]:
    result = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()))
    return list(result.scalars().all())
