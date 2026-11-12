from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class DocumentType(StrEnum):
    CONTRACT = "contract"
    FINANCIAL_REPORT = "financial_report"
    POLICY = "policy"
    AUDIT_EVIDENCE = "audit_evidence"
    COMPLIANCE_MANUAL = "compliance_manual"
    OTHER = "other"


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskCategory(StrEnum):
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    LEGAL = "legal"
    DATA_PRIVACY = "data_privacy"
    VENDOR = "vendor"
    AI_GOVERNANCE = "ai_governance"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Likelihood(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Impact(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class KnowledgeSourceType(StrEnum):
    REGULATION = "regulation"
    POLICY = "policy"
    SOP = "sop"
    CONTROL_FRAMEWORK = "control_framework"
    OTHER = "other"


class ReportFormat(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
