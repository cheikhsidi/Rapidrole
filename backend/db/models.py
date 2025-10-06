import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))

    # Account tier (free, pro, admin)
    account_tier = Column(String(50), default="free", nullable=False, index=True)
    pro_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Gamification
    total_points = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime(timezone=True))

    # Privacy settings
    profile_public = Column(Integer, default=0)  # 0=private, 1=public
    show_in_leaderboard = Column(Integer, default=1)  # opt-in by default
    show_in_feed = Column(Integer, default=1)

    # Referral
    referral_code = Column(String(50), unique=True, index=True)
    referred_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profiles = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    agent_templates = relationship(
        "AgentTemplate", back_populates="creator", cascade="all, delete-orphan"
    )
    referrals = relationship("User", backref="referrer", remote_side=[id])


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Profile data
    resume_text = Column(Text)
    skills = Column(JSON)  # List of skills
    experience = Column(JSON)  # Work history
    education = Column(JSON)
    career_goals = Column(Text)
    preferences = Column(JSON)  # Salary, location, remote, etc.

    # Embeddings (768-dim for text-embedding-3-small)
    skills_embedding = Column(Vector(768))
    experience_embedding = Column(Vector(768))
    goals_embedding = Column(Vector(768))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profiles")

    # Indexes for vector search
    __table_args__ = (
        Index("idx_skills_embedding", "skills_embedding", postgresql_using="ivfflat"),
        Index("idx_experience_embedding", "experience_embedding", postgresql_using="ivfflat"),
    )


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True, index=True)  # Platform-specific ID
    platform = Column(String(100), nullable=False)  # linkedin, indeed, etc.

    # Job details
    title = Column(String(500), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    description = Column(Text)
    requirements = Column(Text)
    url = Column(String(1000))

    # Parsed data
    required_skills = Column(JSON)
    preferred_skills = Column(JSON)
    experience_years = Column(Integer)

    # Embeddings
    description_embedding = Column(Vector(768))
    requirements_embedding = Column(Vector(768))

    # Metadata
    posted_at = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Integer, default=1)

    # Relationships
    applications = relationship("Application", back_populates="job")

    # Indexes
    __table_args__ = (
        Index("idx_company", "company"),
        Index("idx_platform", "platform"),
        Index("idx_description_embedding", "description_embedding", postgresql_using="ivfflat"),
    )


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id"), nullable=False)

    # Application status
    status = Column(String(50), default="draft")  # draft, submitted, interview, rejected, accepted

    # Generated documents
    tailored_resume = Column(Text)
    cover_letter = Column(Text)

    # AI insights
    compatibility_score = Column(Float)
    skill_match_score = Column(Float)
    experience_match_score = Column(Float)
    ai_recommendations = Column(JSON)

    # Tracking
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="applications")
    job = relationship("JobPosting", back_populates="applications")

    # Indexes
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_compatibility_score", "compatibility_score"),
    )


class CompanyIntelligence(Base):
    __tablename__ = "company_intelligence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), unique=True, nullable=False, index=True)

    # Intelligence data
    funding_info = Column(JSON)
    recent_news = Column(JSON)
    culture_insights = Column(Text)
    interview_questions = Column(JSON)
    hiring_patterns = Column(JSON)

    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    data_sources = Column(JSON)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    badge_type = Column(String(100), nullable=False)  # first_app, 10_apps, interview_ace, etc.
    badge_name = Column(String(255), nullable=False)
    badge_description = Column(Text)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="badges")

    # Indexes
    __table_args__ = (Index("idx_user_badge", "user_id", "badge_type", unique=True),)


class AgentTemplate(Base):
    __tablename__ = "agent_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Template details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # resume, cover_letter, job_search, etc.
    template_data = Column(JSON, nullable=False)  # Workflow configuration

    # Engagement metrics
    usage_count = Column(Integer, default=0)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)

    # Visibility
    is_public = Column(Integer, default=1)
    is_featured = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="agent_templates")

    # Indexes
    __table_args__ = (
        Index("idx_template_category", "category"),
        Index("idx_template_public", "is_public"),
        Index("idx_template_featured", "is_featured"),
    )


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Challenge details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    challenge_type = Column(String(100))  # skill, application_speed, etc.
    difficulty = Column(String(50))  # easy, medium, hard

    # Requirements
    requirements = Column(JSON)  # What needs to be done
    reward_points = Column(Integer, default=0)

    # Timing
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))

    # Status
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_challenge_active", "is_active"),
        Index("idx_challenge_dates", "start_date", "end_date"),
    )


class UserChallengeProgress(Base):
    __tablename__ = "user_challenge_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenges.id"), nullable=False)

    # Progress
    progress_data = Column(JSON)  # Current progress
    completed = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True))

    # Metadata
    started_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (Index("idx_user_challenge", "user_id", "challenge_id", unique=True),)


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    referred_email = Column(String(255), nullable=False)
    referred_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Status
    status = Column(String(50), default="pending")  # pending, accepted, rewarded
    reward_claimed = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))

    # Indexes
    __table_args__ = (
        Index("idx_referrer", "referrer_id"),
        Index("idx_referred_email", "referred_email"),
    )


class ActivityFeed(Base):
    __tablename__ = "activity_feed"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Activity details
    activity_type = Column(String(100), nullable=False)  # application, badge, milestone
    activity_data = Column(JSON)  # Anonymized activity details

    # Visibility
    is_public = Column(Integer, default=1)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_activity_type", "activity_type"),
        Index("idx_activity_public", "is_public"),
        Index("idx_activity_created", "created_at"),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    # Subscription details
    plan_type = Column(String(50), default="pro")  # pro, enterprise
    status = Column(String(50), default="active")  # active, cancelled, expired

    # Billing
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))

    # Dates
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))

    # Trial
    trial_start = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_subscription_status", "status"),
        Index("idx_stripe_customer", "stripe_customer_id"),
    )
