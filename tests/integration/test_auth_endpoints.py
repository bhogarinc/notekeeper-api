"""Integration tests for authentication endpoints."""
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User


class TestAuthRegister:
    """Tests for POST /api/v1/auth/register endpoint."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user: User
    ):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "differentuser",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 409
        assert "email already exists" in response.json()["detail"].lower()

    async def test_register_duplicate_username(
        self, client: AsyncClient, test_user: User
    ):
        """Test registration with duplicate username."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 409
        assert "username already exists" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "payload,expected_error",
        [
            ({}, "field required"),
            ({"email": "invalid"}, "valid email"),
            ({"email": "test@example.com"}, "field required"),
            ({"email": "test@example.com", "username": "ab"}, "at least"),
            ({"email": "test@example.com", "username": "test", "password": "123"}, "at least 8"),
            ({"email": "test@example.com", "username": "test user", "password": "password123"}, "alphanumeric"),
        ],
    )
    async def test_register_validation_errors(
        self, client: AsyncClient, payload: dict, expected_error: str
    ):
        """Test input validation for registration."""
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422
        assert expected_error in response.text.lower()


class TestAuthLogin:
    """Tests for POST /api/v1/auth/login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login with invalid password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing required fields."""
        response = await client.post("/api/v1/auth/login", data={})
        assert response.status_code == 422

    async def test_login_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test login with inactive user account."""
        test_user.is_active = False
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()


class TestAuthRefresh:
    """Tests for POST /api/v1/auth/refresh endpoint."""

    async def test_refresh_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh."""
        # First login to get refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]
        
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401

    async def test_refresh_no_token(self, client: AsyncClient):
        """Test refresh without token."""
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

    async def test_refresh_with_access_token(
        self, client: AsyncClient, user_token: str
    ):
        """Test refresh using access token instead of refresh token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        # Should reject access token for refresh
        assert response.status_code == 401


class TestAuthLogout:
    """Tests for POST /api/v1/auth/logout endpoint."""

    async def test_logout_success(self, authorized_client: AsyncClient):
        """Test successful logout."""
        response = await authorized_client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    async def test_logout_no_token(self, client: AsyncClient):
        """Test logout without token."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    async def test_logout_invalid_token(self, client: AsyncClient):
        """Test logout with invalid token."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401

    async def test_logout_expired_token(self, client: AsyncClient, expired_token: str):
        """Test logout with expired token."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401


class TestAuthMe:
    """Tests for GET /api/v1/auth/me endpoint."""

    async def test_get_current_user_success(
        self, authorized_client: AsyncClient, test_user: User
    ):
        """Test get current user with valid token."""
        response = await authorized_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test get current user without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_current_user_expired_token(
        self, client: AsyncClient, expired_token: str
    ):
        """Test get current user with expired token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test get current user with invalid token format."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )
        assert response.status_code == 401


class TestAuthPasswordReset:
    """Tests for password reset endpoints."""

    async def test_request_password_reset_success(
        self, client: AsyncClient, test_user: User
    ):
        """Test password reset request."""
        response = await client.post(
            "/api/v1/auth/password-reset-request",
            json={"email": test_user.email},
        )
        assert response.status_code == 200
        assert "reset link sent" in response.json()["message"].lower()

    async def test_request_password_reset_nonexistent_email(self, client: AsyncClient):
        """Test password reset request with non-existent email."""
        response = await client.post(
            "/api/v1/auth/password-reset-request",
            json={"email": "nonexistent@example.com"},
        )
        # Should return success to prevent email enumeration
        assert response.status_code == 200

    async def test_request_password_reset_invalid_email(self, client: AsyncClient):
        """Test password reset request with invalid email format."""
        response = await client.post(
            "/api/v1/auth/password-reset-request",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422
