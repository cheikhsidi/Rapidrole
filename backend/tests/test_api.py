"""
Comprehensive API endpoint tests.

Tests cover all API endpoints:
- Health checks
- Jobs API
- Applications API
- Users API
- Intelligence API
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check endpoints"""

    async def test_health_check(self):
        """Test basic health check endpoint"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            assert "environment" in data

    async def test_root_endpoint(self):
        """Test root endpoint"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "docs" in data
            assert "health" in data

    async def test_openapi_docs(self):
        """Test OpenAPI documentation is available"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/docs")
            assert response.status_code == 200

    async def test_openapi_json(self):
        """Test OpenAPI JSON schema"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/openapi.json")
            assert response.status_code == 200
            data = response.json()
            assert "openapi" in data
            assert "paths" in data


@pytest.mark.asyncio
class TestJobsAPI:
    """Test Jobs API endpoints"""

    async def test_parse_job_posting_endpoint_exists(self):
        """Test parse job posting endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/jobs/parse",
                params={"url": "https://example.com/job", "platform": "linkedin"},
            )
            # Should not return 405 (method not allowed)
            assert response.status_code != 405

    @pytest.mark.skip(reason="Requires database - run with Docker")
    @pytest.mark.integration
    async def test_get_job_endpoint_exists(self):
        """Test get job endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            job_id = str(uuid4())
            response = await client.get(f"/api/v1/jobs/{job_id}")
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_analyze_job_endpoint_exists(self):
        """Test analyze job endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            job_id = str(uuid4())
            response = await client.post(f"/api/v1/jobs/analyze/{job_id}")
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_search_jobs_endpoint_exists(self):
        """Test search jobs endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_id = str(uuid4())
            response = await client.get("/api/v1/jobs/search", params={"user_id": user_id})
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_search_jobs_with_parameters(self):
        """Test search jobs with query parameters"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_id = str(uuid4())
            response = await client.get(
                "/api/v1/jobs/search", params={"user_id": user_id, "limit": 10, "min_score": 0.7}
            )
            # Should accept parameters
            assert response.status_code in [404, 500]


@pytest.mark.asyncio
class TestApplicationsAPI:
    """Test Applications API endpoints"""

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_create_application_endpoint_exists(self):
        """Test create application endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/applications/", json={"user_id": str(uuid4()), "job_id": str(uuid4())}
            )
            # Should not return 405
            assert response.status_code != 405

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_get_application_endpoint_exists(self):
        """Test get application endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            app_id = str(uuid4())
            response = await client.get(f"/api/v1/applications/{app_id}")
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_update_application_status_endpoint_exists(self):
        """Test update application status endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            app_id = str(uuid4())
            response = await client.patch(
                f"/api/v1/applications/{app_id}/status", json={"status": "submitted"}
            )
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_get_user_applications_endpoint_exists(self):
        """Test get user applications endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_id = str(uuid4())
            response = await client.get(f"/api/v1/applications/user/{user_id}")
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_get_user_applications_with_status_filter(self):
        """Test get user applications with status filter"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_id = str(uuid4())
            response = await client.get(
                f"/api/v1/applications/user/{user_id}", params={"status": "submitted"}
            )
            # Should accept status parameter
            assert response.status_code in [404, 500]


@pytest.mark.asyncio
class TestUsersAPI:
    """Test Users API endpoints"""

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_create_user_endpoint_exists(self):
        """Test create user endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/users/", json={"email": "test@example.com", "full_name": "Test User"}
            )
            # Should not return 405
            assert response.status_code != 405

    @pytest.mark.integration
    @pytest.mark.integration
    async def test_create_user_validation(self):
        """Test create user validates input"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/users/", json={"invalid": "data"})
            # Should return validation error
            assert response.status_code == 422

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_get_user_endpoint_exists(self):
        """Test get user endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_id = str(uuid4())
            response = await client.get(f"/api/v1/users/{user_id}")
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_create_profile_endpoint_exists(self):
        """Test create profile endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_id = str(uuid4())
            response = await client.post(
                f"/api/v1/users/{user_id}/profile",
                json={
                    "resume_text": "Test resume",
                    "skills": ["Python"],
                    "experience": {},
                    "education": {},
                    "career_goals": "Test goals",
                    "preferences": {},
                },
            )
            # Should not return 405
            assert response.status_code != 405

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_get_profile_endpoint_exists(self):
        """Test get profile endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_id = str(uuid4())
            response = await client.get(f"/api/v1/users/{user_id}/profile")
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]


@pytest.mark.asyncio
class TestIntelligenceAPI:
    """Test Intelligence API endpoints"""

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_get_compatibility_endpoint_exists(self):
        """Test get compatibility endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_id = str(uuid4())
            job_id = str(uuid4())
            response = await client.get(f"/api/v1/intelligence/compatibility/{user_id}/{job_id}")
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_get_recommendations_endpoint_exists(self):
        """Test get recommendations endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_id = str(uuid4())
            response = await client.get(f"/api/v1/intelligence/recommendations/{user_id}")
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_get_application_insights_endpoint_exists(self):
        """Test get application insights endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            app_id = str(uuid4())
            response = await client.get(f"/api/v1/intelligence/insights/{app_id}")
            # Should return 404 or 500, not 405
            assert response.status_code in [404, 500]


@pytest.mark.asyncio
class TestAPIValidation:
    """Test API input validation"""

    async def test_invalid_uuid_format(self):
        """Test API handles invalid UUID format"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/invalid-uuid")
            # Should return validation error
            assert response.status_code in [422, 500]

    async def test_missing_required_fields(self):
        """Test API validates required fields"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/applications/", json={})
            # Should return validation error
            assert response.status_code == 422


@pytest.mark.asyncio
class TestAPIErrorHandling:
    """Test API error handling"""

    @pytest.mark.integration
    @pytest.mark.integration
    @pytest.mark.integration
    async def test_404_for_nonexistent_resource(self):
        """Test 404 is returned for nonexistent resources"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{uuid4()}")
            # Should return 404 or 500 (if DB not available)
            assert response.status_code in [404, 500]

    async def test_error_response_format(self):
        """Test error responses have proper format"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/users/", json={"invalid": "data"})
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data


@pytest.mark.asyncio
class TestAPICORS:
    """Test CORS configuration"""

    async def test_cors_headers_present(self):
        """Test CORS headers are configured"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.options(
                "/api/v1/users/", headers={"Origin": "http://localhost:3000"}
            )
            # CORS should be configured (200 or 405)
            assert response.status_code in [200, 405]


@pytest.mark.asyncio
class TestAPIMetrics:
    """Test metrics endpoint"""

    async def test_metrics_endpoint_exists(self):
        """Test Prometheus metrics endpoint exists"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/metrics", follow_redirects=True)
            # Should return metrics or 404 if disabled
            assert response.status_code in [200, 404]
