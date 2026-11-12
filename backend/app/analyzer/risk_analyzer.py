from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models import Analysis, Document, DocumentChunk, Finding
from app.models.enums import AnalysisStatus, DocumentStatus
from app.rag.embeddings import EmbeddingService
from app.rag.store import RAGStore
from app.services.document_parser import chunk_text, parse_document
from app.services.llm import LLMClient
from pathlib import Path

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a senior technology risk, IT audit, and compliance investigator.
Analyze the document against the provided control frameworks and knowledge excerpts.
Identify risks across: compliance, operational, financial, legal, data_privacy, vendor, ai_governance.
Return STRICT JSON with keys: executive_summary, findings, heatmap.
Each finding must include: finding, explanation, supporting_text, page_number, confidence_score (0-1),
category, severity (critical|high|medium|low), probability (high|medium|low), impact (high|medium|low),
recommendation, control_references (array).
Be conservative: only cite supporting_text present in the document excerpts.
"""


class RiskAnalyzer:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.embeddings = EmbeddingService()

    async def run_analysis(self, analysis_id: UUID) -> Analysis:
        result = await self.db.execute(
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .options(selectinload(Analysis.document), selectinload(Analysis.findings))
        )
        analysis = result.scalar_one()
        document = analysis.document

        analysis.status = AnalysisStatus.RUNNING.value
        analysis.started_at = datetime.now(UTC)
        document.status = DocumentStatus.PROCESSING.value
        await self.db.flush()

        try:
            await self._ensure_document_parsed(document)
            rag = RAGStore(self.db, self.embeddings)
            retrieved = await rag.retrieve(
                document.extracted_text[:2000] if document.extracted_text else document.original_filename,
                frameworks=analysis.frameworks,
                top_k=8,
            )
            llm = LLMClient(analysis.llm_provider)
            user_prompt = self._build_prompt(document, retrieved, analysis.frameworks or [])
            payload = await llm.complete_json(SYSTEM_PROMPT, user_prompt)
            await self._persist_results(analysis, payload)
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(UTC)
            document.status = DocumentStatus.ANALYZED.value
            await self.db.flush()
            logger.info("analysis_completed", analysis_id=str(analysis_id), findings=len(analysis.findings))
            return analysis
        except Exception as exc:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(exc)
            analysis.completed_at = datetime.now(UTC)
            document.status = DocumentStatus.FAILED.value
            await self.db.flush()
            logger.exception("analysis_failed", analysis_id=str(analysis_id))
            raise

    async def _ensure_document_parsed(self, document: Document) -> None:
        if document.extracted_text and document.chunks:
            return
        parsed = parse_document(Path(document.storage_path), document.content_type)
        document.extracted_text = parsed.text
        document.page_count = parsed.page_count
        # Clear existing chunks then recreate
        for existing in list(document.chunks):
            await self.db.delete(existing)
        await self.db.flush()
        chunks = chunk_text(parsed.text)
        vectors = await self.embeddings.embed_texts(chunks)
        for idx, (content, vector) in enumerate(zip(chunks, vectors, strict=True)):
            page = self._guess_page(content, parsed.pages)
            self.db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    page_number=page,
                    content=content,
                    token_estimate=len(content.split()),
                    embedding=vector,
                )
            )
        await self.db.flush()

    def _guess_page(self, chunk: str, pages: list[tuple[int, str]]) -> int | None:
        for page_no, page_text in pages:
            if chunk[:80] and chunk[:80] in page_text:
                return page_no
        return pages[0][0] if pages else None

    def _build_prompt(self, document: Document, retrieved: list[dict[str, Any]], frameworks: list[str]) -> str:
        knowledge = "\n\n".join(
            f"[{item.get('framework') or 'KB'} score={item.get('score', 0):.2f}]\n{item['content'][:800]}"
            for item in retrieved
        ) or "No knowledge base excerpts available."
        doc_excerpt = (document.extracted_text or "")[:12000]
        return (
            f"Frameworks: {', '.join(frameworks)}\n"
            f"Document: {document.original_filename}\n\n"
            f"=== Knowledge Base Excerpts ===\n{knowledge}\n\n"
            f"=== Document Excerpts ===\n{doc_excerpt}\n"
        )

    async def _persist_results(self, analysis: Analysis, payload: dict[str, Any]) -> None:
        analysis.executive_summary = payload.get("executive_summary")
        analysis.heatmap = payload.get("heatmap")
        for existing in list(analysis.findings):
            await self.db.delete(existing)
        await self.db.flush()

        for idx, item in enumerate(payload.get("findings", []), start=1):
            key_src = f"{item.get('finding','')}-{item.get('page_number')}-{idx}"
            finding_key = hashlib.sha1(key_src.encode()).hexdigest()[:12]
            self.db.add(
                Finding(
                    analysis_id=analysis.id,
                    finding_key=finding_key,
                    finding=item.get("finding", "Untitled finding"),
                    explanation=item.get("explanation", ""),
                    supporting_text=item.get("supporting_text", ""),
                    page_number=item.get("page_number"),
                    confidence_score=float(item.get("confidence_score", 0.5)),
                    category=str(item.get("category", "compliance")).lower(),
                    severity=str(item.get("severity", "medium")).lower(),
                    probability=str(item.get("probability", "medium")).lower(),
                    impact=str(item.get("impact", "medium")).lower(),
                    recommendation=item.get("recommendation"),
                    control_references=item.get("control_references"),
                )
            )
        await self.db.flush()
