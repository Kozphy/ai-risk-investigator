from __future__ import annotations

import json
from typing import Any

import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    def __init__(self, provider: str | None = None) -> None:
        self.settings = get_settings()
        self.provider = provider or self.settings.default_llm_provider
        if self.provider == "openai" and not self.settings.openai_api_key and not self.settings.demo_mode:
            raise ValueError("OPENAI_API_KEY required")
        if self.provider == "anthropic" and not self.settings.anthropic_api_key and not self.settings.demo_mode:
            raise ValueError("ANTHROPIC_API_KEY required")

    @property
    def model_name(self) -> str:
        if self.provider == "openai":
            return self.settings.openai_model
        if self.provider == "anthropic":
            return self.settings.anthropic_model
        return "mock-risk-analyzer-v1"

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        if self.provider == "mock" or (
            self.settings.demo_mode and not (self.settings.openai_api_key or self.settings.anthropic_api_key)
        ):
            return self._mock_response(user)
        if self.provider == "openai":
            return await self._openai_json(system, user)
        if self.provider == "anthropic":
            return await self._anthropic_json(system, user)
        raise ValueError(f"Unsupported provider: {self.provider}")

    async def _openai_json(self, system: str, user: str) -> dict[str, Any]:
        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        response = await client.chat.completions.create(
            model=self.settings.openai_model,
            temperature=self.settings.llm_temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    async def _anthropic_json(self, system: str, user: str) -> dict[str, Any]:
        client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        response = await client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=self.settings.max_analysis_tokens,
            temperature=self.settings.llm_temperature,
            system=system + "\nRespond with valid JSON only.",
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        return json.loads(text)

    def _mock_response(self, user: str) -> dict[str, Any]:
        snippet = user[:240].replace("\n", " ")
        return {
            "executive_summary": {
                "top_risks": [
                    "Indemnity and liability caps may be commercially unbalanced",
                    "Data processing clause lacks explicit retention limits",
                    "Vendor access controls are vaguely defined",
                ],
                "key_observations": [
                    "Document contains standard commercial terms with several ambiguous risk transfer clauses",
                    "Privacy and AI-related obligations are incomplete relative to GDPR / AI Act expectations",
                ],
                "recommended_actions": [
                    "Negotiate liability cap symmetry and carve-outs for willful misconduct",
                    "Add data retention, subprocessors, and breach notification SLAs",
                    "Require SOC 2 / ISO 27001 evidence for vendor access",
                ],
                "heatmap_summary": "Elevated legal and data privacy risk; medium operational and vendor risk.",
            },
            "findings": [
                {
                    "finding": "Asymmetric indemnity and unlimited liability exposure",
                    "explanation": "One-sided indemnity without reciprocal caps creates material financial and legal risk.",
                    "supporting_text": snippet or "The Provider shall indemnify the Customer without limitation...",
                    "page_number": 1,
                    "confidence_score": 0.86,
                    "category": "legal",
                    "severity": "high",
                    "probability": "medium",
                    "impact": "high",
                    "recommendation": "Introduce mutual indemnity and a negotiated liability cap with carve-outs.",
                    "control_references": ["COSO Principle 10", "SOX ICFR risk assessment"],
                },
                {
                    "finding": "Insufficient personal data retention controls",
                    "explanation": "Absence of retention schedules conflicts with GDPR storage limitation principle.",
                    "supporting_text": "Personal data may be processed as needed for the services.",
                    "page_number": 2,
                    "confidence_score": 0.81,
                    "category": "data_privacy",
                    "severity": "high",
                    "probability": "high",
                    "impact": "high",
                    "recommendation": "Define retention periods, deletion workflows, and DPIA triggers.",
                    "control_references": ["GDPR Art. 5(1)(e)", "ISO 27001 A.8.10"],
                },
                {
                    "finding": "AI system usage lacks governance commitments",
                    "explanation": "If AI features are used, transparency and human oversight obligations are unspecified.",
                    "supporting_text": "Automated tools may be used to improve service delivery.",
                    "page_number": 3,
                    "confidence_score": 0.74,
                    "category": "ai_governance",
                    "severity": "medium",
                    "probability": "medium",
                    "impact": "medium",
                    "recommendation": "Add AI Act-aligned transparency, logging, and human oversight clauses.",
                    "control_references": ["EU AI Act Art. 13", "Internal AI Policy"],
                },
                {
                    "finding": "Vendor remote access not constrained",
                    "explanation": "Broad access language without MFA / least-privilege requirements elevates vendor risk.",
                    "supporting_text": "Vendor personnel may access systems as required.",
                    "page_number": 2,
                    "confidence_score": 0.79,
                    "category": "vendor",
                    "severity": "medium",
                    "probability": "medium",
                    "impact": "high",
                    "recommendation": "Mandate MFA, least privilege, access reviews, and logging.",
                    "control_references": ["ISO 27001 A.5.19", "ISO 27001 A.8.2"],
                },
            ],
            "heatmap": {
                "legal": {"severity": "high", "probability": "medium"},
                "data_privacy": {"severity": "high", "probability": "high"},
                "vendor": {"severity": "medium", "probability": "medium"},
                "ai_governance": {"severity": "medium", "probability": "medium"},
                "compliance": {"severity": "medium", "probability": "medium"},
                "financial": {"severity": "low", "probability": "low"},
                "operational": {"severity": "medium", "probability": "low"},
            },
        }


async def healthcheck_llm() -> dict[str, Any]:
    settings = get_settings()
    return {
        "provider": settings.default_llm_provider,
        "openai_configured": bool(settings.openai_api_key),
        "anthropic_configured": bool(settings.anthropic_api_key),
        "demo_mode": settings.demo_mode,
    }
