from __future__ import annotations

import hashlib
import math
from typing import Sequence

from openai import AsyncOpenAI

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.settings.openai_api_key and self.settings.default_llm_provider != "mock":
            client = AsyncOpenAI(api_key=self.settings.openai_api_key)
            response = await client.embeddings.create(
                model=self.settings.embedding_model,
                input=list(texts),
                dimensions=self.settings.embedding_dimensions,
            )
            return [item.embedding for item in response.data]
        return [self._deterministic_embedding(text) for text in texts]

    def _deterministic_embedding(self, text: str) -> list[float]:
        """Local deterministic pseudo-embedding for demo / offline / CI."""
        dim = self.settings.embedding_dimensions
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        seed = digest
        while len(values) < dim:
            seed = hashlib.sha256(seed).digest()
            for b in seed:
                values.append((b / 255.0) * 2 - 1)
                if len(values) >= dim:
                    break
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]
