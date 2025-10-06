"""
Pytest configuration and fixtures for testing.

Provides:
- Test database setup
- Mock fixtures
- Common test utilities
"""

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest

# Load test environment variables before importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["APP_ENV"] = "test"

# Now safe to import after env is set
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import models to register them with Base.metadata
import db.models  # noqa: F401
from db.database import Base, get_db
from main import app

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine():
    """Create a test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def test_client(test_db_session):
    """Create a test client with database override"""

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    from unittest.mock import Mock

    response = Mock()
    response.content = '{"result": "success"}'
    response.data = [Mock(embedding=[0.1] * 768)]
    response.usage = Mock(total_tokens=100)
    return response


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response"""
    from unittest.mock import Mock

    response = Mock()
    response.content = "Generated cover letter text"
    return response


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {"email": "test@example.com", "full_name": "Test User"}


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        "resume_text": "Experienced software engineer",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience": {
            "total_years": 5,
            "positions": [
                {"title": "Senior Developer", "company": "Tech Corp", "duration": "3 years"}
            ],
        },
        "education": {"degree": "BS Computer Science", "university": "State University"},
        "career_goals": "Build innovative AI products",
        "preferences": {"salary_min": 120000, "remote": True, "locations": ["Remote"]},
    }


@pytest.fixture
def sample_job_data():
    """Sample job data for testing"""
    return {
        "external_id": "job-123",
        "platform": "linkedin",
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "location": "Remote",
        "description": "We're looking for a senior Python developer",
        "requirements": "5+ years Python, FastAPI, PostgreSQL",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "url": "https://example.com/job/123",
    }
