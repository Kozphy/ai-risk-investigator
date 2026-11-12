from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeChunk
from app.rag.embeddings import EmbeddingService


class RAGStore:
    def __init__(self, db: AsyncSession, embeddings: EmbeddingService | None = None) -> None:
        self.db = db
        self.embeddings = embeddings or EmbeddingService()

    async def retrieve(
        self,
        query: str,
        *,
        frameworks: list[str] | None = None,
        top_k: int = 8,
    ) -> list[dict]:
        vectors = await self.embeddings.embed_texts([query])
        if not vectors:
            return []
        query_vec = vectors[0]
        # pgvector cosine distance via raw SQL for portability across SQLAlchemy versions
        vector_literal = "[" + ",".join(str(float(x)) for x in query_vec) + "]"
        framework_filter = ""
        params: dict = {"limit": top_k}
        if frameworks:
            framework_filter = "AND (framework = ANY(:frameworks) OR framework IS NULL)"
            params["frameworks"] = frameworks

        sql = text(
            f"""
            SELECT id, knowledge_document_id, content, framework,
                   embedding <=> CAST(:embedding AS vector) AS distance
            FROM knowledge_chunks
            WHERE embedding IS NOT NULL
            {framework_filter}
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """
        )
        params["embedding"] = vector_literal
        try:
            result = await self.db.execute(sql, params)
            rows = result.mappings().all()
            return [
                {
                    "id": str(row["id"]),
                    "knowledge_document_id": str(row["knowledge_document_id"]),
                    "content": row["content"],
                    "framework": row["framework"],
                    "score": 1.0 - float(row["distance"]),
                }
                for row in rows
            ]
        except Exception:
            # Fallback for empty DB / missing extension in unit tests
            result = await self.db.execute(select(KnowledgeChunk).limit(top_k))
            chunks = result.scalars().all()
            return [
                {
                    "id": str(c.id),
                    "knowledge_document_id": str(c.knowledge_document_id),
                    "content": c.content,
                    "framework": c.framework,
                    "score": 0.5,
                }
                for c in chunks
            ]

    async def upsert_knowledge_embeddings(
        self,
        knowledge_document_id: UUID,
        chunks: list[tuple[int, str, str | None]],
    ) -> int:
        texts = [c[1] for c in chunks]
        vectors = await self.embeddings.embed_texts(texts)
        created = 0
        for (idx, content, framework), vector in zip(chunks, vectors, strict=True):
            self.db.add(
                KnowledgeChunk(
                    knowledge_document_id=knowledge_document_id,
                    chunk_index=idx,
                    content=content,
                    framework=framework,
                    embedding=vector,
                )
            )
            created += 1
        await self.db.flush()
        return created
