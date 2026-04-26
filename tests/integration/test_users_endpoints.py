"""Integration tests for users endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestUsersGet:
    """Tests for GET /api/v1/users/me endpoint."""

    async def test_get_current_user_success(
        self, authorized_client: AsyncClient, test_user: User
    ):
        """Test successful retrieval of current user."""
        response = await authorized_client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert "password" not in data
        assert "hashed_password" not in data
        assert "created_at" in data

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test get current user without authentication."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_get_current_user_expired_token(
        self, client: AsyncClient, expired_token: str
    ):
        """Test get current user with expired token."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401


class TestUsersUpdate:
    """Tests for PUT /api/v1/users/me endpoint."""

    async def test_update_user_success(
        self, authorized_client: AsyncClient, test_user: User
    ):
        """Test successful user profile update."""
        response = await authorized_client.put(
            "/api/v1/users/me",
            json={
                "username": "updatedusername",
                "email": "updated@example.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updatedusername"
        assert data["email"] == "updated@example.com"

    async def test_update_user_partial(
        self, authorized_client: AsyncClient, test_user: User
    ):
        """Test partial user update."""
        original_email = test_user.email
        response = await authorized_client.put(
            "/api/v1/users/me",
            json={"username": "newusername"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newusername"
        assert data["email"] == original_email

    async def test_update_user_duplicate_email(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test update with duplicate email."""
        from app.core.security import get_password_hash
        
        # Create another user
        other_user = User(
            email="existing@example.com",
            username="existinguser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        await db_session.commit()

        # Try to update to existing email
        response = await authorized_client.put(
            "/api/v1/users/me",
            json={"email": "existing@example.com"},
        )
        assert response.status_code == 409

    async def test_update_user_duplicate_username(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test update with duplicate username."""
        from app.core.security import get_password_hash
        
        # Create another user
        other_user = User(
            email="othername@example.com",
            username="takenusername",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        await db_session.commit()

        response = await authorized_client.put(
            "/api/v1/users/me",
            json={"username": "takenusername"},
        )
        assert response.status_code == 409

    @pytest.mark.parametrize(
        "payload,expected_error",
        [
            ({"email": "invalid-email"}, "valid email"),
            ({"username": "ab"}, "at least"),
            ({"username": "invalid username"}, "alphanumeric"),
        ],
    )
    async def test_update_user_validation(
        self, authorized_client: AsyncClient, payload: dict, expected_error: str
    ):
        """Test user update validation errors."""
        response = await authorized_client.put("/api/v1/users/me", json=payload)
        assert response.status_code == 422
        assert expected_error in response.text.lower()

    async def test_update_user_unauthorized(self, client: AsyncClient):
        """Test user update without authentication."""
        response = await client.put(
            "/api/v1/users/me",
            json={"username": "newname"},
        )
        assert response.status_code == 401


class TestUsersChangePassword:
    """Tests for PUT /api/v1/users/me/password endpoint."""

    async def test_change_password_success(
        self, authorized_client: AsyncClient, test_user: User
    ):
        """Test successful password change."""
        response = await authorized_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "testpassword123",
                "new_password": "NewSecurePass456!",
            },
        )
        assert response.status_code == 200
        assert "password updated" in response.json()["message"].lower()

    async def test_change_password_wrong_current(
        self, authorized_client: AsyncClient
    ):
        """Test password change with wrong current password."""
        response = await authorized_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "wrongpassword",
                "new_password": "NewSecurePass456!",
            },
        )
        assert response.status_code == 400
        assert "incorrect password" in response.json()["detail"].lower()

    async def test_change_password_same_as_current(
        self, authorized_client: AsyncClient
    ):
        """Test password change with same password."""
        response = await authorized_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "testpassword123",
                "new_password": "testpassword123",
            },
        )
        assert response.status_code == 400
        assert "different from current" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "payload,expected_error",
        [
            ({"new_password": "short"}, "at least 8"),
            ({"current_password": "testpassword123"}, "field required"),
            ({"current_password": "testpassword123", "new_password": "password"}, "complexity"),
        ],
    )
    async def test_change_password_validation(
        self, authorized_client: AsyncClient, payload: dict, expected_error: str
    ):
        """Test password change validation."""
        response = await authorized_client.put(
            "/api/v1/users/me/password", json=payload
        )
        assert response.status_code == 422
        assert expected_error in response.text.lower()

    async def test_change_password_unauthorized(self, client: AsyncClient):
        """Test password change without authentication."""
        response = await client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "oldpass",
                "new_password": "newpass123",
            },
        )
        assert response.status_code == 401


class TestUsersDelete:
    """Tests for DELETE /api/v1/users/me endpoint."""

    async def test_delete_user_success(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test successful user deletion."""
        response = await authorized_client.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": "testpassword123"},
        )
        assert response.status_code == 204

    async def test_delete_user_wrong_password(
        self, authorized_client: AsyncClient
    ):
        """Test user deletion with wrong password."""
        response = await authorized_client.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": "wrongpassword"},
        )
        assert response.status_code == 400
        assert "incorrect password" in response.json()["detail"].lower()

    async def test_delete_user_missing_password(
        self, authorized_client: AsyncClient
    ):
        """Test user deletion without password confirmation."""
        response = await authorized_client.delete("/api/v1/users/me")
        assert response.status_code == 422

    async def test_delete_user_unauthorized(self, client: AsyncClient):
        """Test user deletion without authentication."""
        response = await client.delete("/api/v1/users/me")
        assert response.status_code == 401


class TestAdminUsers:
    """Tests for admin user management endpoints."""

    async def test_admin_list_users_success(
        self,
        client: AsyncClient,
        superuser_token: str,
    ):
        """Test admin listing all users."""
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {superuser_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_admin_list_users_pagination(
        self,
        client: AsyncClient,
        superuser_token: str,
    ):
        """Test admin users list pagination."""
        response = await client.get(
            "/api/v1/admin/users?page=1&size=10",
            headers={"Authorization": f"Bearer {superuser_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10

    async def test_admin_list_users_non_admin(
        self, authorized_client: AsyncClient
    ):
        """Test non-admin cannot list all users."""
        response = await authorized_client.get("/api/v1/admin/users")
        assert response.status_code == 403

    async def test_admin_get_user_success(
        self,
        client: AsyncClient,
        superuser_token: str,
        test_user: User,
    ):
        """Test admin getting specific user."""
        response = await client.get(
            f"/api/v1/admin/users/{test_user.id}",
            headers={"Authorization": f"Bearer {superuser_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)

    async def test_admin_get_user_not_found(
        self, client: AsyncClient, superuser_token: str
    ):
        """Test admin getting non-existent user."""
        response = await client.get(
            f"/api/v1/admin/users/{uuid4()}",
            headers={"Authorization": f"Bearer {superuser_token}"},
        )
        assert response.status_code == 404

    async def test_admin_update_user_success(
        self,
        client: AsyncClient,
        superuser_token: str,
        test_user: User,
    ):
        """Test admin updating user."""
        response = await client.put(
            f"/api/v1/admin/users/{test_user.id}",
            headers={"Authorization": f"Bearer {superuser_token}"},
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    async def test_admin_delete_user_success(
        self,
        client: AsyncClient,
        superuser_token: str,
        db_session: AsyncSession,
    ):
        """Test admin deleting user."""
        from app.core.security import get_password_hash
        
        # Create user to delete
        user_to_delete = User(
            email="delete@example.com",
            username="deleteuser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(user_to_delete)
        await db_session.commit()
        await db_session.refresh(user_to_delete)

        response = await client.delete(
            f"/api/v1/admin/users/{user_to_delete.id}",
            headers={"Authorization": f"Bearer {superuser_token}"},
        )
        assert response.status_code == 204
