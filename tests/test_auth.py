"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient

from utils.auth import get_password_hash, verify_password


@pytest.mark.unit
class TestAuthRegistration:
    """Test user registration."""

    async def test_register_success(self, test_client: AsyncClient):
        """Test successful user registration."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, test_client: AsyncClient):
        """Test registration with duplicate email."""
        # Register first user
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
                "full_name": "First User",
            },
        )

        # Try to register again with same email
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "DifferentPass123!",
                "full_name": "Second User",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_weak_password(self, test_client: AsyncClient):
        """Test registration with weak password."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "weakpass@example.com",
                "password": "short",
                "full_name": "Weak Pass User",
            },
        )

        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"]

    async def test_register_invalid_email(self, test_client: AsyncClient):
        """Test registration with invalid email."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "full_name": "Invalid Email",
            },
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.unit
class TestAuthLogin:
    """Test user login."""

    async def test_login_success(self, test_client: AsyncClient):
        """Test successful login."""
        # Register user first
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "SecurePass123!",
                "full_name": "Login Test",
            },
        )

        # Login
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, test_client: AsyncClient):
        """Test login with wrong password."""
        # Register user
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "CorrectPass123!",
                "full_name": "Wrong Pass Test",
            },
        )

        # Try to login with wrong password
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPass123!",
            },
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, test_client: AsyncClient):
        """Test login with non-existent user."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePass123!",
            },
        )

        assert response.status_code == 401


@pytest.mark.unit
class TestAuthTokens:
    """Test token operations."""

    async def test_get_current_user(self, test_client: AsyncClient):
        """Test getting current user info."""
        # Register and get token
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "tokentest@example.com",
                "password": "SecurePass123!",
                "full_name": "Token Test",
            },
        )
        access_token = register_response.json()["access_token"]

        # Get current user
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "tokentest@example.com"
        assert data["full_name"] == "Token Test"
        assert data["account_tier"] == "free"

    async def test_get_current_user_invalid_token(self, test_client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401

    async def test_get_current_user_no_token(self, test_client: AsyncClient):
        """Test getting current user without token."""
        response = await test_client.get("/api/v1/auth/me")

        assert response.status_code == 403  # Forbidden without auth header

    async def test_refresh_token(self, test_client: AsyncClient):
        """Test refreshing access token."""
        # Register and get tokens
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "refreshtest@example.com",
                "password": "SecurePass123!",
                "full_name": "Refresh Test",
            },
        )
        refresh_token = register_response.json()["refresh_token"]

        # Refresh token
        response = await test_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_with_access_token(self, test_client: AsyncClient):
        """Test that access token cannot be used for refresh."""
        # Register and get tokens
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongtokentype@example.com",
                "password": "SecurePass123!",
                "full_name": "Wrong Token Type",
            },
        )
        access_token = register_response.json()["access_token"]

        # Try to refresh with access token
        response = await test_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 401


@pytest.mark.unit
class TestPasswordChange:
    """Test password change functionality."""

    async def test_change_password_success(self, test_client: AsyncClient):
        """Test successful password change."""
        # Register user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "changepass@example.com",
                "password": "OldPass123!",
                "full_name": "Change Pass Test",
            },
        )
        access_token = register_response.json()["access_token"]

        # Change password
        response = await test_client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "OldPass123!",
                "new_password": "NewPass123!",
            },
        )

        assert response.status_code == 200

        # Verify can login with new password
        login_response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "changepass@example.com",
                "password": "NewPass123!",
            },
        )
        assert login_response.status_code == 200

    async def test_change_password_wrong_current(self, test_client: AsyncClient):
        """Test password change with wrong current password."""
        # Register user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongcurrent@example.com",
                "password": "CorrectPass123!",
                "full_name": "Wrong Current Test",
            },
        )
        access_token = register_response.json()["access_token"]

        # Try to change with wrong current password
        response = await test_client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "WrongPass123!",
                "new_password": "NewPass123!",
            },
        )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    async def test_change_password_same_as_current(self, test_client: AsyncClient):
        """Test password change with same password."""
        # Register user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "samepass@example.com",
                "password": "SamePass123!",
                "full_name": "Same Pass Test",
            },
        )
        access_token = register_response.json()["access_token"]

        # Try to change to same password
        response = await test_client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "SamePass123!",
                "new_password": "SamePass123!",
            },
        )

        assert response.status_code == 400
        assert "different" in response.json()["detail"].lower()


@pytest.mark.unit
class TestPasswordReset:
    """Test password reset functionality."""

    async def test_forgot_password(self, test_client: AsyncClient):
        """Test forgot password request."""
        # Register user
        await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "forgot@example.com",
                "password": "OldPass123!",
                "full_name": "Forgot Test",
            },
        )

        # Request password reset
        response = await test_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "forgot@example.com"},
        )

        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()

    async def test_forgot_password_nonexistent_email(self, test_client: AsyncClient):
        """Test forgot password with non-existent email (should still return success)."""
        response = await test_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )

        # Should return success to prevent email enumeration
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)

        # Verify correct password
        assert verify_password(password, hashed)

        # Verify wrong password
        assert not verify_password("WrongPassword123!", hashed)

    def test_different_hashes(self):
        """Test that same password produces different hashes."""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


@pytest.mark.unit
class TestLogout:
    """Test logout functionality."""

    async def test_logout(self, test_client: AsyncClient):
        """Test logout endpoint."""
        # Register and get token
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout@example.com",
                "password": "SecurePass123!",
                "full_name": "Logout Test",
            },
        )
        access_token = register_response.json()["access_token"]

        # Logout
        response = await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
