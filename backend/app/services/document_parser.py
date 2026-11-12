from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


@dataclass
class ParsedDocument:
    text: str
    page_count: int
    pages: list[tuple[int, str]]


def parse_document(path: Path, content_type: str | None = None) -> ParsedDocument:
    suffix = path.suffix.lower()
    if suffix == ".pdf" or (content_type and "pdf" in content_type):
        return _parse_pdf(path)
    if suffix == ".docx" or (content_type and "wordprocessingml" in (content_type or "")):
        return _parse_docx(path)
    if suffix == ".txt" or (content_type and content_type.startswith("text/")):
        return _parse_txt(path)
    raise ValueError(f"Unsupported document type: {suffix or content_type}")


def _parse_pdf(path: Path) -> ParsedDocument:
    reader = PdfReader(str(path))
    pages: list[tuple[int, str]] = []
    for idx, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        pages.append((idx, text))
    full = "\n\n".join(f"[Page {n}]\n{t}" for n, t in pages if t)
    return ParsedDocument(text=full, page_count=len(reader.pages), pages=pages)


def _parse_docx(path: Path) -> ParsedDocument:
    doc = DocxDocument(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)
    # DOCX has no reliable page map; treat as single logical page.
    return ParsedDocument(text=text, page_count=1, pages=[(1, text)])


def _parse_txt(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return ParsedDocument(text=text, page_count=1, pages=[(1, text)])


def chunk_text(text: str, *, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks
