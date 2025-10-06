"""Convert privacy settings to boolean

Revision ID: 003
Revises: 002
Create Date: 2025-10-05

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert Integer privacy columns to Boolean."""
    # For PostgreSQL, we can alter the column type and convert values
    # SQLite doesn't support ALTER COLUMN, so we'd need to recreate the table
    # This migration handles PostgreSQL

    # Convert profile_public: 0 -> False, 1 -> True
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN profile_public TYPE BOOLEAN
        USING CASE WHEN profile_public = 0 THEN FALSE ELSE TRUE END
        """
    )
    op.alter_column("users", "profile_public", nullable=False)

    # Convert show_in_leaderboard: 0 -> False, 1 -> True
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN show_in_leaderboard TYPE BOOLEAN
        USING CASE WHEN show_in_leaderboard = 0 THEN FALSE ELSE TRUE END
        """
    )
    op.alter_column("users", "show_in_leaderboard", nullable=False)

    # Convert show_in_feed: 0 -> False, 1 -> True
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN show_in_feed TYPE BOOLEAN
        USING CASE WHEN show_in_feed = 0 THEN FALSE ELSE TRUE END
        """
    )
    op.alter_column("users", "show_in_feed", nullable=False)


def downgrade() -> None:
    """Convert Boolean privacy columns back to Integer."""
    # Convert back to Integer: False -> 0, True -> 1

    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN profile_public TYPE INTEGER
        USING CASE WHEN profile_public THEN 1 ELSE 0 END
        """
    )

    op.execute(
        """
        ALTER TABLE userss
        ALTER COLUMN show_in_leaderboard TYPE INTEGER
        USING CASE WHEN show_in_leaderboard THEN 1 ELSE 0 END
        """
    )

    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN show_in_feed TYPE INTEGER
        USING CASE WHEN show_in_feed THEN 1 ELSE 0 END
        """
    )
