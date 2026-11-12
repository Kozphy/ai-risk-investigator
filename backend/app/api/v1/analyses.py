from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.analyzer.risk_analyzer import RiskAnalyzer
from app.api.deps import CurrentUser, DbSession, audit
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models import Analysis, Document, Finding
from app.models.enums import AnalysisStatus
from app.schemas.analysis import AnalysisCreate, AnalysisOut, DashboardStats, FindingOut

router = APIRouter(prefix="/analyses", tags=["analyses"])


async def _run_analysis_job(analysis_id: UUID) -> None:
    async with AsyncSessionLocal() as session:
        try:
            analyzer = RiskAnalyzer(session)
            await analyzer.run_analysis(analysis_id)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.post("", response_model=AnalysisOut, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    payload: AnalysisCreate,
    background: BackgroundTasks,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> Analysis:
    result = await db.execute(
        select(Document).where(Document.id == payload.document_id, Document.owner_id == user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    settings = get_settings()
    provider = payload.llm_provider or settings.default_llm_provider
    model = settings.openai_model if provider == "openai" else (
        settings.anthropic_model if provider == "anthropic" else "mock-risk-analyzer-v1"
    )
    analysis = Analysis(
        document_id=document.id,
        created_by=user.id,
        status=AnalysisStatus.PENDING.value,
        llm_provider=provider,
        llm_model=model,
        frameworks=payload.frameworks,
    )
    db.add(analysis)
    await db.flush()
    await audit(request, db, user, "analysis.create", "analysis", str(analysis.id))
    background.add_task(_run_analysis_job, analysis.id)
    analysis.findings = []
    return analysis


@router.get("", response_model=list[AnalysisOut])
async def list_analyses(db: DbSession, user: CurrentUser) -> list[Analysis]:
    result = await db.execute(
        select(Analysis)
        .where(Analysis.created_by == user.id)
        .options(selectinload(Analysis.findings))
        .order_by(Analysis.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats(db: DbSession, user: CurrentUser) -> DashboardStats:
    doc_count = await db.scalar(
        select(func.count()).select_from(Document).where(Document.owner_id == user.id)
    )
    analysis_count = await db.scalar(
        select(func.count()).select_from(Analysis).where(Analysis.created_by == user.id)
    )
    finding_rows = await db.execute(
        select(Finding.category, Finding.severity, Finding.created_at)
        .join(Analysis, Analysis.id == Finding.analysis_id)
        .where(Analysis.created_by == user.id)
    )
    rows = finding_rows.all()
    by_cat: dict[str, int] = {}
    by_sev: dict[str, int] = {}
    trend_map: dict[str, int] = {}
    for category, severity, created_at in rows:
        by_cat[category] = by_cat.get(category, 0) + 1
        by_sev[severity] = by_sev.get(severity, 0) + 1
        day = (created_at or datetime.now(UTC)).date().isoformat()
        trend_map[day] = trend_map.get(day, 0) + 1
    trend = [{"date": k, "findings": v} for k, v in sorted(trend_map.items())]
    return DashboardStats(
        document_volume=int(doc_count or 0),
        analysis_count=int(analysis_count or 0),
        finding_count=len(rows),
        risks_by_category=by_cat,
        risks_by_severity=by_sev,
        trend_over_time=trend,
    )


@router.get("/{analysis_id}", response_model=AnalysisOut)
async def get_analysis(analysis_id: UUID, db: DbSession, user: CurrentUser) -> Analysis:
    result = await db.execute(
        select(Analysis)
        .where(Analysis.id == analysis_id, Analysis.created_by == user.id)
        .options(selectinload(Analysis.findings))
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/{analysis_id}/findings", response_model=list[FindingOut])
async def list_findings(analysis_id: UUID, db: DbSession, user: CurrentUser) -> list[Finding]:
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.created_by == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Analysis not found")
    findings = await db.execute(
        select(Finding).where(Finding.analysis_id == analysis_id).order_by(Finding.severity)
    )
    return list(findings.scalars().all())
