"""Initial schema with pgvector support

Revision ID: 001
Revises:
Create Date: 2025-10-05

"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSON, UUID

from alembic import op

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Users table
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # User profiles table
    op.create_table(
        "user_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resume_text", sa.Text),
        sa.Column("skills", JSON),
        sa.Column("experience", JSON),
        sa.Column("education", JSON),
        sa.Column("career_goals", sa.Text),
        sa.Column("preferences", JSON),
        sa.Column("skills_embedding", Vector(768)),
        sa.Column("experience_embedding", Vector(768)),
        sa.Column("goals_embedding", Vector(768)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Job postings table
    op.create_table(
        "job_postings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(255), unique=True),
        sa.Column("platform", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("salary_min", sa.Integer),
        sa.Column("salary_max", sa.Integer),
        sa.Column("description", sa.Text),
        sa.Column("requirements", sa.Text),
        sa.Column("url", sa.String(1000)),
        sa.Column("required_skills", JSON),
        sa.Column("preferred_skills", JSON),
        sa.Column("experience_years", sa.Integer),
        sa.Column("description_embedding", Vector(768)),
        sa.Column("requirements_embedding", Vector(768)),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_active", sa.Integer, default=1),
    )
    op.create_index("idx_job_postings_external_id", "job_postings", ["external_id"])
    op.create_index("idx_job_postings_company", "job_postings", ["company"])
    op.create_index("idx_job_postings_platform", "job_postings", ["platform"])

    # Applications table
    op.create_table(
        "applications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("job_postings.id"), nullable=False),
        sa.Column("status", sa.String(50), default="draft"),
        sa.Column("tailored_resume", sa.Text),
        sa.Column("cover_letter", sa.Text),
        sa.Column("compatibility_score", sa.Float),
        sa.Column("skill_match_score", sa.Float),
        sa.Column("experience_match_score", sa.Float),
        sa.Column("ai_recommendations", JSON),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("idx_applications_user_status", "applications", ["user_id", "status"])
    op.create_index("idx_applications_compatibility", "applications", ["compatibility_score"])

    # Company intelligence table
    op.create_table(
        "company_intelligence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=False, unique=True),
        sa.Column("funding_info", JSON),
        sa.Column("recent_news", JSON),
        sa.Column("culture_insights", sa.Text),
        sa.Column("interview_questions", JSON),
        sa.Column("hiring_patterns", JSON),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("data_sources", JSON),
    )
    op.create_index("idx_company_intelligence_name", "company_intelligence", ["company_name"])


def downgrade() -> None:
    op.drop_table("company_intelligence")
    op.drop_table("applications")
    op.drop_table("job_postings")
    op.drop_table("user_profiles")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
