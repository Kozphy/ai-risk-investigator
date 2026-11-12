"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBED_DIM = 3072


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("organization", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("document_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("page_count", sa.Integer()),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("extracted_text", sa.Text()),
        sa.Column("meta", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_checksum_sha256", "documents", ["checksum_sha256"])

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE")),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_estimate", sa.Integer()),
        sa.Column("embedding", Vector(EMBED_DIM)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])

    op.create_table(
        "knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("framework", sa.String(128)),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_documents_framework", "knowledge_documents", ["framework"])

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "knowledge_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("framework", sa.String(128)),
        sa.Column("embedding", Vector(EMBED_DIM)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_chunks_knowledge_document_id", "knowledge_chunks", ["knowledge_document_id"])
    op.create_index("ix_knowledge_chunks_framework", "knowledge_chunks", ["framework"])

    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("llm_provider", sa.String(32), nullable=False),
        sa.Column("llm_model", sa.String(128), nullable=False),
        sa.Column("frameworks", sa.JSON()),
        sa.Column("executive_summary", sa.JSON()),
        sa.Column("heatmap", sa.JSON()),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analyses_document_id", "analyses", ["document_id"])
    op.create_index("ix_analyses_created_by", "analyses", ["created_by"])
    op.create_index("ix_analyses_status", "analyses", ["status"])

    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id", ondelete="CASCADE")),
        sa.Column("finding_key", sa.String(64), nullable=False),
        sa.Column("finding", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("supporting_text", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("probability", sa.String(32), nullable=False),
        sa.Column("impact", sa.String(32), nullable=False),
        sa.Column("recommendation", sa.Text()),
        sa.Column("control_references", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("analysis_id", "finding_key", name="uq_findings_analysis_key"),
    )
    op.create_index("ix_findings_analysis_id", "findings", ["analysis_id"])
    op.create_index("ix_findings_category", "findings", ["category"])
    op.create_index("ix_findings_severity", "findings", ["severity"])

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id", ondelete="CASCADE")),
        sa.Column("format", sa.String(16), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reports_analysis_id", "reports", ["analysis_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64)),
        sa.Column("resource_id", sa.String(64)),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("user_agent", sa.String(512)),
        sa.Column("details", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # IVFFlat optional; cosine distance ops require lists after data exists.
    op.execute(
        """
        DO $$ BEGIN
          CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding
          ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        EXCEPTION WHEN others THEN
          RAISE NOTICE 'Skipping ivfflat index (needs data or extension support)';
        END $$;
        """
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("reports")
    op.drop_table("findings")
    op.drop_table("analyses")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("users")
