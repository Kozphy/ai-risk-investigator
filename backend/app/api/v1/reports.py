from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, audit
from app.models import Analysis, Report
from app.reporting.generator import ReportGenerator
from app.schemas.analysis import ReportCreate, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=201)
async def create_report(
    payload: ReportCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> ReportOut:
    result = await db.execute(
        select(Analysis).where(Analysis.id == payload.analysis_id, Analysis.created_by == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Analysis not found")
    generator = ReportGenerator(db)
    report = await generator.generate(payload.analysis_id, payload.format, user.id)
    await audit(request, db, user, "report.create", "report", str(report.id), {"format": payload.format.value})
    return ReportOut(
        id=report.id,
        analysis_id=report.analysis_id,
        format=report.format,
        file_size=report.file_size,
        created_at=report.created_at,
        download_url=f"/api/v1/reports/{report.id}/download",
    )


@router.get("/{report_id}/download")
async def download_report(report_id: UUID, db: DbSession, user: CurrentUser) -> FileResponse:
    result = await db.execute(select(Report).where(Report.id == report_id, Report.created_by == user.id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    path = Path(report.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file missing")
    media = (
        "application/pdf"
        if report.format == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(path, media_type=media, filename=path.name)
