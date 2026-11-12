from pathlib import Path

from app.services.document_parser import chunk_text, parse_document


def test_parse_txt(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("Line one.\n\nLiability shall be unlimited for Provider.", encoding="utf-8")
    parsed = parse_document(path)
    assert parsed.page_count == 1
    assert "Liability" in parsed.text


def test_chunk_text_overlap() -> None:
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    assert len(chunks) >= 3
    assert chunks[0][-50:] in chunks[1] or chunks[1].startswith(chunks[0][-100:])
