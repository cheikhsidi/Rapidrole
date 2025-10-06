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
    # For PostgreSQL, we need to drop defaults before changing type
    # Then convert values and set new defaults

    # Convert profile_public: 0 -> False, 1 -> True
    op.execute("ALTER TABLE users ALTER COLUMN profile_public DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN profile_public TYPE BOOLEAN
        USING CASE WHEN profile_public = 0 THEN FALSE ELSE TRUE END
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN profile_public SET DEFAULT TRUE")

    # Convert show_in_leaderboard: 0 -> False, 1 -> True
    op.execute("ALTER TABLE users ALTER COLUMN show_in_leaderboard DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN show_in_leaderboard TYPE BOOLEAN
        USING CASE WHEN show_in_leaderboard = 0 THEN FALSE ELSE TRUE END
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN show_in_leaderboard SET DEFAULT TRUE")

    # Convert show_in_feed: 0 -> False, 1 -> True
    op.execute("ALTER TABLE users ALTER COLUMN show_in_feed DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN show_in_feed TYPE BOOLEAN
        USING CASE WHEN show_in_feed = 0 THEN FALSE ELSE TRUE END
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN show_in_feed SET DEFAULT TRUE")


def downgrade() -> None:
    """Convert Boolean privacy columns back to Integer."""
    # Convert back to Integer: False -> 0, True -> 1
    # Drop boolean defaults and set integer defaults

    op.execute("ALTER TABLE users ALTER COLUMN profile_public DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN profile_public TYPE INTEGER
        USING CASE WHEN profile_public THEN 1 ELSE 0 END
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN profile_public SET DEFAULT 1")

    op.execute("ALTER TABLE users ALTER COLUMN show_in_leaderboard DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN show_in_leaderboard TYPE INTEGER
        USING CASE WHEN show_in_leaderboard THEN 1 ELSE 0 END
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN show_in_leaderboard SET DEFAULT 1")

    op.execute("ALTER TABLE users ALTER COLUMN show_in_feed DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN show_in_feed TYPE INTEGER
        USING CASE WHEN show_in_feed THEN 1 ELSE 0 END
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN show_in_feed SET DEFAULT 1")
