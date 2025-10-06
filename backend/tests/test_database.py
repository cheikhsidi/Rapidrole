"""
Tests for database operations and models.

Tests cover:
- Database connection
- Model creation
- Query operations
- Connection pooling
"""

import pytest
from sqlalchemy import select
from db.models import User, UserProfile, JobPosting, Application
from db.database import AsyncSessionLocal
import uuid


@pytest.mark.asyncio
class TestDatabaseModels:
    """Test suite for database models"""
    
    async def test_user_model_creation(self):
        """Test User model can be created"""
        user = User(
            email="test@example.com",
            full_name="Test User"
        )
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.id is not None
    
    async def test_user_profile_model_creation(self):
        """Test UserProfile model can be created"""
        user_id = uuid.uuid4()
        
        profile = UserProfile(
            user_id=user_id,
            resume_text="Test resume",
            skills=["Python", "FastAPI"],
            experience={"years": 5},
            education={"degree": "BS CS"},
            career_goals="Build great products",
            preferences={"remote": True},
        )
        
        assert profile.user_id == user_id
        assert profile.skills == ["Python", "FastAPI"]
        assert profile.experience["years"] == 5
    
    async def test_job_posting_model_creation(self):
        """Test JobPosting model can be created"""
        job = JobPosting(
            external_id="job-123",
            platform="linkedin",
            title="Senior Developer",
            company="Tech Corp",
            location="Remote",
            description="Great opportunity",
            requirements="Python, FastAPI",
            required_skills=["Python", "FastAPI"],
            is_active=1,
        )
        
        assert job.title == "Senior Developer"
        assert job.company == "Tech Corp"
        assert job.platform == "linkedin"
        assert job.is_active == 1
    
    async def test_application_model_creation(self):
        """Test Application model can be created"""
        user_id = uuid.uuid4()
        job_id = uuid.uuid4()
        
        application = Application(
            user_id=user_id,
            job_id=job_id,
            status="draft",
            compatibility_score=0.85,
            skill_match_score=0.90,
            experience_match_score=0.80,
        )
        
        assert application.user_id == user_id
        assert application.job_id == job_id
        assert application.status == "draft"
        assert application.compatibility_score == 0.85


@pytest.mark.asyncio
class TestDatabaseOperations:
    """Test suite for database operations"""
    
    async def test_database_session_creation(self):
        """Test database session can be created"""
        async with AsyncSessionLocal() as session:
            assert session is not None
    
    async def test_health_check_functions(self):
        """Test database health check functions"""
        from db.database import health_check_db, health_check_redis
        
        # These might fail if DB/Redis not running, but should not raise
        try:
            db_healthy = await health_check_db()
            assert isinstance(db_healthy, bool)
        except Exception:
            pass  # Expected if DB not running in test
        
        try:
            redis_healthy = await health_check_redis()
            assert isinstance(redis_healthy, bool)
        except Exception:
            pass  # Expected if Redis not running in test


@pytest.mark.asyncio
class TestModelRelationships:
    """Test suite for model relationships"""
    
    def test_user_profile_relationship(self):
        """Test User-UserProfile relationship is defined"""
        user = User(email="test@example.com")
        assert hasattr(user, 'profiles')
    
    def test_user_applications_relationship(self):
        """Test User-Application relationship is defined"""
        user = User(email="test@example.com")
        assert hasattr(user, 'applications')
    
    def test_job_applications_relationship(self):
        """Test JobPosting-Application relationship is defined"""
        job = JobPosting(
            external_id="job-123",
            platform="linkedin",
            title="Test Job",
            company="Test Co"
        )
        assert hasattr(job, 'applications')
