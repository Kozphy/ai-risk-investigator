from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import DocumentStatus, DocumentType, KnowledgeSourceType


class DocumentOut(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    file_size: int
    document_type: DocumentType
    status: DocumentStatus
    page_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeOut(BaseModel):
    id: UUID
    title: str
    source_type: KnowledgeSourceType
    framework: str | None
    filename: str
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeUploadMeta(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    source_type: KnowledgeSourceType = KnowledgeSourceType.REGULATION
    framework: str | None = None
