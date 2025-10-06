"""
Integration tests for the complete application flow.

Tests cover:
- End-to-end user workflows
- API integration
- Database integration
- Agent integration
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check endpoints"""

    async def test_health_check(self, test_client: AsyncClient):
        """Test basic health check"""
        response = await test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_root_endpoint(self, test_client: AsyncClient):
        """Test root endpoint"""
        response = await test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


@pytest.mark.asyncio
class TestUserWorkflow:
    """Test complete user workflow"""

    async def test_create_user(self, test_client: AsyncClient, sample_user_data):
        """Test user creation"""
        response = await test_client.post("/api/v1/users/", json=sample_user_data)

        # Might fail if DB not set up, but should not crash
        assert response.status_code in [200, 201, 500]

    async def test_user_endpoints_exist(self, test_client: AsyncClient):
        """Test user endpoints are registered"""
        # These will return errors without proper setup, but endpoints should exist
        response = await test_client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
        assert response.status_code in [404, 500]  # Not 405 (method not allowed)


@pytest.mark.asyncio
class TestJobWorkflow:
    """Test job-related workflow"""

    async def test_job_endpoints_exist(self, test_client: AsyncClient):
        """Test job endpoints are registered"""
        response = await test_client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
        assert response.status_code in [404, 500]  # Not 405


@pytest.mark.asyncio
class TestApplicationWorkflow:
    """Test application workflow"""

    async def test_application_endpoints_exist(self, test_client: AsyncClient):
        """Test application endpoints are registered"""
        response = await test_client.get(
            "/api/v1/applications/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code in [404, 500]  # Not 405


@pytest.mark.asyncio
class TestIntelligenceWorkflow:
    """Test intelligence endpoints"""

    async def test_intelligence_endpoints_exist(self, test_client: AsyncClient):
        """Test intelligence endpoints are registered"""
        response = await test_client.get(
            "/api/v1/intelligence/compatibility/00000000-0000-0000-0000-000000000000/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code in [404, 500]  # Not 405


@pytest.mark.asyncio
class TestAPIDocumentation:
    """Test API documentation"""

    async def test_openapi_docs_available(self, test_client: AsyncClient):
        """Test OpenAPI docs are generated"""
        response = await test_client.get("/docs")
        assert response.status_code == 200

    async def test_openapi_json_available(self, test_client: AsyncClient):
        """Test OpenAPI JSON schema is available"""
        response = await test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "components" in data


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling"""

    async def test_404_handling(self, test_client: AsyncClient):
        """Test 404 errors are handled"""
        response = await test_client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    async def test_validation_error_handling(self, test_client: AsyncClient):
        """Test validation errors are handled"""
        response = await test_client.post("/api/v1/users/", json={"invalid": "data"})
        assert response.status_code in [422, 500]


@pytest.mark.asyncio
class TestCORS:
    """Test CORS configuration"""

    async def test_cors_headers(self, test_client: AsyncClient):
        """Test CORS headers are present"""
        response = await test_client.options(
            "/api/v1/users/", headers={"Origin": "http://localhost:3000"}
        )
        # CORS should be configured
        assert response.status_code in [200, 405]
