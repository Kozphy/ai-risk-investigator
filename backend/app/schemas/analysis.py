from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import AnalysisStatus, Impact, Likelihood, ReportFormat, RiskCategory, Severity


class AnalysisCreate(BaseModel):
    document_id: UUID
    frameworks: list[str] = Field(default_factory=lambda: ["SOX", "ISO 27001", "COSO", "GDPR", "AI Act"])
    llm_provider: str | None = None


class FindingOut(BaseModel):
    id: UUID
    finding_key: str
    finding: str
    explanation: str
    supporting_text: str
    page_number: int | None
    confidence_score: float
    category: RiskCategory
    severity: Severity
    probability: Likelihood
    impact: Impact
    recommendation: str | None
    control_references: list[str] | None

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    id: UUID
    document_id: UUID
    status: AnalysisStatus
    llm_provider: str
    llm_model: str
    frameworks: list[str] | None
    executive_summary: dict[str, Any] | None
    heatmap: dict[str, Any] | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    findings: list[FindingOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ReportCreate(BaseModel):
    analysis_id: UUID
    format: ReportFormat = ReportFormat.PDF


class ReportOut(BaseModel):
    id: UUID
    analysis_id: UUID
    format: ReportFormat
    file_size: int
    created_at: datetime
    download_url: str | None = None

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    document_volume: int
    analysis_count: int
    finding_count: int
    risks_by_category: dict[str, int]
    risks_by_severity: dict[str, int]
    trend_over_time: list[dict[str, Any]]
