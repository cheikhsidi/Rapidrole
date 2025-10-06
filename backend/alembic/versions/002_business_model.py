"""Add business model tables (freemium, community, gamification)

Revision ID: 002
Revises: 001
Create Date: 2025-10-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update users table with new fields
    op.add_column('users', sa.Column('account_tier', sa.String(50), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('pro_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('total_points', sa.Integer, nullable=False, server_default='0'))
    op.add_column('users', sa.Column('current_streak', sa.Integer, nullable=False, server_default='0'))
    op.add_column('users', sa.Column('longest_streak', sa.Integer, nullable=False, server_default='0'))
    op.add_column('users', sa.Column('last_activity_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('profile_public', sa.Integer, nullable=False, server_default='0'))
    op.add_column('users', sa.Column('show_in_leaderboard', sa.Integer, nullable=False, server_default='1'))
    op.add_column('users', sa.Column('show_in_feed', sa.Integer, nullable=False, server_default='1'))
    op.add_column('users', sa.Column('referral_code', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('referred_by', UUID(as_uuid=True), nullable=True))
    
    op.create_index('idx_users_account_tier', 'users', ['account_tier'])
    op.create_index('idx_users_referral_code', 'users', ['referral_code'], unique=True)
    op.create_foreign_key('fk_users_referred_by', 'users', 'users', ['referred_by'], ['id'])
    
    # User badges table
    op.create_table(
        'user_badges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('badge_type', sa.String(100), nullable=False),
        sa.Column('badge_name', sa.String(255), nullable=False),
        sa.Column('badge_description', sa.Text),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_user_badge', 'user_badges', ['user_id', 'badge_type'], unique=True)
    
    # Agent templates table
    op.create_table(
        'agent_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('creator_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(100)),
        sa.Column('template_data', JSON, nullable=False),
        sa.Column('usage_count', sa.Integer, server_default='0'),
        sa.Column('upvotes', sa.Integer, server_default='0'),
        sa.Column('downvotes', sa.Integer, server_default='0'),
        sa.Column('is_public', sa.Integer, server_default='1'),
        sa.Column('is_featured', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('idx_template_category', 'agent_templates', ['category'])
    op.create_index('idx_template_public', 'agent_templates', ['is_public'])
    op.create_index('idx_template_featured', 'agent_templates', ['is_featured'])
    
    # Challenges table
    op.create_table(
        'challenges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('challenge_type', sa.String(100)),
        sa.Column('difficulty', sa.String(50)),
        sa.Column('requirements', JSON),
        sa.Column('reward_points', sa.Integer, server_default='0'),
        sa.Column('start_date', sa.DateTime(timezone=True)),
        sa.Column('end_date', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Integer, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_challenge_active', 'challenges', ['is_active'])
    op.create_index('idx_challenge_dates', 'challenges', ['start_date', 'end_date'])
    
    # User challenge progress table
    op.create_table(
        'user_challenge_progress',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('challenge_id', UUID(as_uuid=True), sa.ForeignKey('challenges.id'), nullable=False),
        sa.Column('progress_data', JSON),
        sa.Column('completed', sa.Integer, server_default='0'),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_user_challenge', 'user_challenge_progress', ['user_id', 'challenge_id'], unique=True)
    
    # Referrals table
    op.create_table(
        'referrals',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('referrer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('referred_email', sa.String(255), nullable=False),
        sa.Column('referred_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('reward_claimed', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('accepted_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_referrer', 'referrals', ['referrer_id'])
    op.create_index('idx_referred_email', 'referrals', ['referred_email'])
    
    # Activity feed table
    op.create_table(
        'activity_feed',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('activity_type', sa.String(100), nullable=False),
        sa.Column('activity_data', JSON),
        sa.Column('is_public', sa.Integer, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_activity_type', 'activity_feed', ['activity_type'])
    op.create_index('idx_activity_public', 'activity_feed', ['is_public'])
    op.create_index('idx_activity_created', 'activity_feed', ['created_at'])
    
    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('plan_type', sa.String(50), server_default='pro'),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('stripe_customer_id', sa.String(255)),
        sa.Column('stripe_subscription_id', sa.String(255)),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('current_period_start', sa.DateTime(timezone=True)),
        sa.Column('current_period_end', sa.DateTime(timezone=True)),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('trial_start', sa.DateTime(timezone=True)),
        sa.Column('trial_end', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('idx_subscription_status', 'subscriptions', ['status'])
    op.create_index('idx_stripe_customer', 'subscriptions', ['stripe_customer_id'])


def downgrade() -> None:
    # Drop new tables
    op.drop_table('subscriptions')
    op.drop_table('activity_feed')
    op.drop_table('referrals')
    op.drop_table('user_challenge_progress')
    op.drop_table('challenges')
    op.drop_table('agent_templates')
    op.drop_table('user_badges')
    
    # Remove columns from users table
    op.drop_constraint('fk_users_referred_by', 'users', type_='foreignkey')
    op.drop_index('idx_users_referral_code', 'users')
    op.drop_index('idx_users_account_tier', 'users')
    op.drop_column('users', 'referred_by')
    op.drop_column('users', 'referral_code')
    op.drop_column('users', 'show_in_feed')
    op.drop_column('users', 'show_in_leaderboard')
    op.drop_column('users', 'profile_public')
    op.drop_column('users', 'last_activity_date')
    op.drop_column('users', 'longest_streak')
    op.drop_column('users', 'current_streak')
    op.drop_column('users', 'total_points')
    op.drop_column('users', 'pro_expires_at')
    op.drop_column('users', 'account_tier')
