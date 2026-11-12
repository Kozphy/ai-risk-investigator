import pytest

from app.services.llm import LLMClient


@pytest.mark.asyncio
async def test_mock_llm_returns_findings(monkeypatch) -> None:
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "mock")
    monkeypatch.setenv("DEMO_MODE", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()
    client = LLMClient("mock")
    payload = await client.complete_json("system", "Sample contract with unlimited indemnity.")
    assert "findings" in payload
    assert payload["findings"][0]["confidence_score"] > 0
    assert "executive_summary" in payload
    get_settings.cache_clear()
