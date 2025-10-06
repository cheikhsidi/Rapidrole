"""
Pytest configuration and fixtures for testing.

Provides:
- Test database setup
- Mock fixtures
- Common test utilities
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from main import app
from db.database import Base, get_db
from config.settings import settings


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
    
    async with AsyncClient(app=app, base_url="http://test") as client:
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
    return {
        "email": "test@example.com",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        "resume_text": "Experienced software engineer",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience": {
            "total_years": 5,
            "positions": [
                {
                    "title": "Senior Developer",
                    "company": "Tech Corp",
                    "duration": "3 years"
                }
            ]
        },
        "education": {
            "degree": "BS Computer Science",
            "university": "State University"
        },
        "career_goals": "Build innovative AI products",
        "preferences": {
            "salary_min": 120000,
            "remote": True,
            "locations": ["Remote"]
        }
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
        "url": "https://example.com/job/123"
    }
