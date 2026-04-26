"""Integration tests for categories endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Category
from app.models.user import User


class TestCategoriesCreate:
    """Tests for POST /api/v1/categories endpoint."""

    async def test_create_category_success(self, authorized_client: AsyncClient):
        """Test successful category creation."""
        response = await authorized_client.post(
            "/api/v1/categories",
            json={
                "name": "Work Tasks",
                "description": "Work related notes and tasks",
                "color": "#4A90E2",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Work Tasks"
        assert data["description"] == "Work related notes and tasks"
        assert data["color"] == "#4A90E2"
        assert "id" in data
        assert "created_at" in data

    async def test_create_category_minimal(self, authorized_client: AsyncClient):
        """Test category creation with minimal fields."""
        response = await authorized_client.post(
            "/api/v1/categories",
            json={"name": "Simple Category"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Category"
        assert data["description"] is None
        assert data["color"] is None

    async def test_create_category_unauthorized(self, client: AsyncClient):
        """Test category creation without authentication."""
        response = await client.post(
            "/api/v1/categories",
            json={"name": "Unauthorized Category"},
        )
        assert response.status_code == 401

    async def test_create_category_duplicate_name(
        self, authorized_client: AsyncClient, test_category: Category
    ):
        """Test category creation with duplicate name."""
        response = await authorized_client.post(
            "/api/v1/categories",
            json={"name": test_category.name},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "payload,expected_error",
        [
            ({}, "field required"),
            ({"name": ""}, "at least 1 character"),
            ({"name": "a" * 51}, "at most 50 characters"),
            ({"name": "Valid", "color": "invalid"}, "valid hex color"),
            ({"name": "Valid", "color": "#GGGGGG"}, "valid hex color"),
        ],
    )
    async def test_create_category_validation(
        self, authorized_client: AsyncClient, payload: dict, expected_error: str
    ):
        """Test category creation validation errors."""
        response = await authorized_client.post("/api/v1/categories", json=payload)
        assert response.status_code == 422
        assert expected_error in response.text.lower()


class TestCategoriesList:
    """Tests for GET /api/v1/categories endpoint."""

    async def test_list_categories_success(
        self, authorized_client: AsyncClient, test_category: Category
    ):
        """Test successful categories listing."""
        response = await authorized_client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(c["id"] == str(test_category.id) for c in data)

    async def test_list_categories_includes_note_count(
        self,
        authorized_client: AsyncClient,
        test_category: Category,
        test_note,
    ):
        """Test that categories include note count."""
        response = await authorized_client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        category = next(c for c in data if c["id"] == str(test_category.id))
        assert "note_count" in category
        assert category["note_count"] >= 1

    async def test_list_categories_unauthorized(self, client: AsyncClient):
        """Test categories listing without authentication."""
        response = await client.get("/api/v1/categories")
        assert response.status_code == 401

    async def test_list_categories_isolated_by_user(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that users only see their own categories."""
        from app.core.security import get_password_hash
        
        # Create another user and category
        other_user = User(
            email="othercat@example.com",
            username="othercatuser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_category = Category(
            name="Other User Category",
            user_id=other_user.id,
        )
        db_session.add(other_category)
        await db_session.commit()

        # Current user should not see other user's category
        response = await authorized_client.get("/api/v1/categories")
        data = response.json()
        assert not any(c["name"] == "Other User Category" for c in data)


class TestCategoriesGet:
    """Tests for GET /api/v1/categories/{category_id} endpoint."""

    async def test_get_category_success(
        self, authorized_client: AsyncClient, test_category: Category
    ):
        """Test successful category retrieval."""
        response = await authorized_client.get(
            f"/api/v1/categories/{test_category.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_category.id)
        assert data["name"] == test_category.name
        assert "notes" in data or "note_count" in data

    async def test_get_category_not_found(self, authorized_client: AsyncClient):
        """Test retrieval of non-existent category."""
        response = await authorized_client.get(f"/api/v1/categories/{uuid4()}")
        assert response.status_code == 404

    async def test_get_category_invalid_id(self, authorized_client: AsyncClient):
        """Test retrieval with invalid category ID."""
        response = await authorized_client.get("/api/v1/categories/invalid-uuid")
        assert response.status_code == 422

    async def test_get_category_other_users_category(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test retrieval of another user's category (should fail)."""
        from app.core.security import get_password_hash
        
        other_user = User(
            email="otherget@example.com",
            username="othergetuser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_category = Category(
            name="Private Category",
            user_id=other_user.id,
        )
        db_session.add(other_category)
        await db_session.commit()
        await db_session.refresh(other_category)

        response = await authorized_client.get(
            f"/api/v1/categories/{other_category.id}"
        )
        assert response.status_code == 404


class TestCategoriesUpdate:
    """Tests for PUT /api/v1/categories/{category_id} endpoint."""

    async def test_update_category_success(
        self, authorized_client: AsyncClient, test_category: Category
    ):
        """Test successful category update."""
        response = await authorized_client.put(
            f"/api/v1/categories/{test_category.id}",
            json={
                "name": "Updated Category Name",
                "description": "Updated description",
                "color": "#E94B3C",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category Name"
        assert data["description"] == "Updated description"
        assert data["color"] == "#E94B3C"

    async def test_update_category_partial(
        self, authorized_client: AsyncClient, test_category: Category
    ):
        """Test partial category update."""
        original_name = test_category.name
        response = await authorized_client.put(
            f"/api/v1/categories/{test_category.id}",
            json={"description": "New description only"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == original_name
        assert data["description"] == "New description only"

    async def test_update_category_not_found(self, authorized_client: AsyncClient):
        """Test update of non-existent category."""
        response = await authorized_client.put(
            f"/api/v1/categories/{uuid4()}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 404

    async def test_update_category_duplicate_name(
        self,
        authorized_client: AsyncClient,
        test_category: Category,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test update with duplicate category name."""
        # Create another category
        other_category = Category(
            name="Another Category",
            user_id=test_user.id,
        )
        db_session.add(other_category)
        await db_session.commit()

        # Try to rename to existing name
        response = await authorized_client.put(
            f"/api/v1/categories/{other_category.id}",
            json={"name": test_category.name},
        )
        assert response.status_code == 409


class TestCategoriesDelete:
    """Tests for DELETE /api/v1/categories/{category_id} endpoint."""

    async def test_delete_category_success(
        self, authorized_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test successful category deletion."""
        # Create a category without notes
        category = Category(
            name="Deletable Category",
            user_id=test_user.id,
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        response = await authorized_client.delete(
            f"/api/v1/categories/{category.id}"
        )
        assert response.status_code == 204

        # Verify deletion
        get_response = await authorized_client.get(
            f"/api/v1/categories/{category.id}"
        )
        assert get_response.status_code == 404

    async def test_delete_category_with_notes(
        self,
        authorized_client: AsyncClient,
        test_category: Category,
        test_note,
    ):
        """Test deletion of category with associated notes."""
        response = await authorized_client.delete(
            f"/api/v1/categories/{test_category.id}"
        )
        # Should either prevent deletion or cascade
        assert response.status_code in [204, 409]

    async def test_delete_category_not_found(self, authorized_client: AsyncClient):
        """Test deletion of non-existent category."""
        response = await authorized_client.delete(f"/api/v1/categories/{uuid4()}")
        assert response.status_code == 404

    async def test_delete_category_unauthorized(
        self, client: AsyncClient, test_category: Category
    ):
        """Test category deletion without authentication."""
        response = await client.delete(f"/api/v1/categories/{test_category.id}")
        assert response.status_code == 401
