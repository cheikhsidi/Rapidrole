"""Add user password and email verification fields

Revision ID: 004
Revises: 003
Create Date: 2025-10-06

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add authentication and email verification columns to users table."""
    # Add password column
    op.add_column("users", sa.Column("hashed_password", sa.String(255), nullable=True))

    # Add email verification columns
    op.add_column(
        "users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false")
    )
    op.add_column("users", sa.Column("verification_token", sa.String(255), nullable=True))
    op.add_column(
        "users", sa.Column("verification_token_expires", sa.DateTime(timezone=True), nullable=True)
    )

    # Add password reset columns
    op.add_column("users", sa.Column("reset_token", sa.String(255), nullable=True))
    op.add_column(
        "users", sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True)
    )

    # Set a default password hash for existing users (they'll need to reset)
    # This is a hash of "ChangeMe123!" - existing users should reset their password
    op.execute(
        """
        UPDATE users
        SET hashed_password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/1jrYK'
        WHERE hashed_password IS NULL
        """
    )

    # Now make password non-nullable
    op.alter_column("users", "hashed_password", nullable=False)

    # Add indexes for token lookups
    op.create_index("idx_verification_token", "users", ["verification_token"])
    op.create_index("idx_reset_token", "users", ["reset_token"])


def downgrade() -> None:
    """Remove authentication and email verification columns from users table."""
    op.drop_index("idx_reset_token", "users")
    op.drop_index("idx_verification_token", "users")
    op.drop_column("users", "reset_token_expires")
    op.drop_column("users", "reset_token")
    op.drop_column("users", "verification_token_expires")
    op.drop_column("users", "verification_token")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "hashed_password")
