"""Integration tests for tags endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Tag
from app.models.user import User


class TestTagsCreate:
    """Tests for POST /api/v1/tags endpoint."""

    async def test_create_tag_success(self, authorized_client: AsyncClient):
        """Test successful tag creation."""
        response = await authorized_client.post(
            "/api/v1/tags",
            json={
                "name": "important",
                "color": "#FF0000",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "important"
        assert data["color"] == "#FF0000"
        assert "id" in data
        assert "created_at" in data

    async def test_create_tag_minimal(self, authorized_client: AsyncClient):
        """Test tag creation with minimal fields."""
        response = await authorized_client.post(
            "/api/v1/tags",
            json={"name": "minimal-tag"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "minimal-tag"
        assert data["color"] is None

    async def test_create_tag_unauthorized(self, client: AsyncClient):
        """Test tag creation without authentication."""
        response = await client.post(
            "/api/v1/tags",
            json={"name": "unauthorized-tag"},
        )
        assert response.status_code == 401

    async def test_create_tag_duplicate_name(
        self, authorized_client: AsyncClient, test_tag: Tag
    ):
        """Test tag creation with duplicate name."""
        response = await authorized_client.post(
            "/api/v1/tags",
            json={"name": test_tag.name},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "payload,expected_error",
        [
            ({}, "field required"),
            ({"name": ""}, "at least 1 character"),
            ({"name": "a" * 31}, "at most 30 characters"),
            ({"name": "valid-name"}, None),  # Valid - should succeed
            ({"name": "Invalid Name"}, "alphanumeric"),  # Spaces not allowed
            ({"name": "valid", "color": "invalid"}, "valid hex color"),
        ],
    )
    async def test_create_tag_validation(
        self, authorized_client: AsyncClient, payload: dict, expected_error: str
    ):
        """Test tag creation validation errors."""
        response = await authorized_client.post("/api/v1/tags", json=payload)
        if expected_error is None:
            assert response.status_code == 201
        else:
            assert response.status_code == 422
            assert expected_error in response.text.lower()

    async def test_create_tag_case_insensitive_unique(
        self, authorized_client: AsyncClient, test_tag: Tag
    ):
        """Test that tag names are case-insensitive unique."""
        response = await authorized_client.post(
            "/api/v1/tags",
            json={"name": test_tag.name.upper()},
        )
        assert response.status_code == 409


class TestTagsList:
    """Tests for GET /api/v1/tags endpoint."""

    async def test_list_tags_success(
        self, authorized_client: AsyncClient, test_tag: Tag
    ):
        """Test successful tags listing."""
        response = await authorized_client.get("/api/v1/tags")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(t["id"] == str(test_tag.id) for t in data)

    async def test_list_tags_includes_note_count(
        self,
        authorized_client: AsyncClient,
        test_tag: Tag,
        test_note,
    ):
        """Test that tags include note count."""
        response = await authorized_client.get("/api/v1/tags")
        assert response.status_code == 200
        data = response.json()
        tag = next(t for t in data if t["id"] == str(test_tag.id))
        assert "note_count" in tag
        assert tag["note_count"] >= 1

    async def test_list_tags_unauthorized(self, client: AsyncClient):
        """Test tags listing without authentication."""
        response = await client.get("/api/v1/tags")
        assert response.status_code == 401

    async def test_list_tags_isolated_by_user(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that users only see their own tags."""
        from app.core.security import get_password_hash
        
        # Create another user and tag
        other_user = User(
            email="othertag@example.com",
            username="othertaguser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_tag = Tag(
            name="other-user-tag",
            user_id=other_user.id,
        )
        db_session.add(other_tag)
        await db_session.commit()

        # Current user should not see other user's tag
        response = await authorized_client.get("/api/v1/tags")
        data = response.json()
        assert not any(t["name"] == "other-user-tag" for t in data)


class TestTagsGet:
    """Tests for GET /api/v1/tags/{tag_id} endpoint."""

    async def test_get_tag_success(
        self, authorized_client: AsyncClient, test_tag: Tag
    ):
        """Test successful tag retrieval."""
        response = await authorized_client.get(f"/api/v1/tags/{test_tag.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_tag.id)
        assert data["name"] == test_tag.name
        assert "note_count" in data or "notes" in data

    async def test_get_tag_not_found(self, authorized_client: AsyncClient):
        """Test retrieval of non-existent tag."""
        response = await authorized_client.get(f"/api/v1/tags/{uuid4()}")
        assert response.status_code == 404

    async def test_get_tag_invalid_id(self, authorized_client: AsyncClient):
        """Test retrieval with invalid tag ID."""
        response = await authorized_client.get("/api/v1/tags/invalid-uuid")
        assert response.status_code == 422

    async def test_get_tag_other_users_tag(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test retrieval of another user's tag (should fail)."""
        from app.core.security import get_password_hash
        
        other_user = User(
            email="othertagget@example.com",
            username="othertaggetuser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_tag = Tag(
            name="private-tag",
            user_id=other_user.id,
        )
        db_session.add(other_tag)
        await db_session.commit()
        await db_session.refresh(other_tag)

        response = await authorized_client.get(f"/api/v1/tags/{other_tag.id}")
        assert response.status_code == 404


class TestTagsUpdate:
    """Tests for PUT /api/v1/tags/{tag_id} endpoint."""

    async def test_update_tag_success(
        self, authorized_client: AsyncClient, test_tag: Tag
    ):
        """Test successful tag update."""
        response = await authorized_client.put(
            f"/api/v1/tags/{test_tag.id}",
            json={
                "name": "updated-tag-name",
                "color": "#00FF00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-tag-name"
        assert data["color"] == "#00FF00"

    async def test_update_tag_partial(
        self, authorized_client: AsyncClient, test_tag: Tag
    ):
        """Test partial tag update."""
        original_name = test_tag.name
        response = await authorized_client.put(
            f"/api/v1/tags/{test_tag.id}",
            json={"color": "#0000FF"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == original_name
        assert data["color"] == "#0000FF"

    async def test_update_tag_not_found(self, authorized_client: AsyncClient):
        """Test update of non-existent tag."""
        response = await authorized_client.put(
            f"/api/v1/tags/{uuid4()}",
            json={"name": "updated-name"},
        )
        assert response.status_code == 404

    async def test_update_tag_duplicate_name(
        self,
        authorized_client: AsyncClient,
        test_tag: Tag,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test update with duplicate tag name."""
        # Create another tag
        other_tag = Tag(
            name="another-tag",
            user_id=test_user.id,
        )
        db_session.add(other_tag)
        await db_session.commit()

        # Try to rename to existing name
        response = await authorized_client.put(
            f"/api/v1/tags/{other_tag.id}",
            json={"name": test_tag.name},
        )
        assert response.status_code == 409

    async def test_update_tag_invalid_name(
        self, authorized_client: AsyncClient, test_tag: Tag
    ):
        """Test tag update with invalid name format."""
        response = await authorized_client.put(
            f"/api/v1/tags/{test_tag.id}",
            json={"name": "Invalid Tag Name"},
        )
        assert response.status_code == 422


class TestTagsDelete:
    """Tests for DELETE /api/v1/tags/{tag_id} endpoint."""

    async def test_delete_tag_success(
        self, authorized_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test successful tag deletion."""
        # Create a tag without notes
        tag = Tag(
            name="deletable-tag",
            user_id=test_user.id,
        )
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        response = await authorized_client.delete(f"/api/v1/tags/{tag.id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = await authorized_client.get(f"/api/v1/tags/{tag.id}")
        assert get_response.status_code == 404

    async def test_delete_tag_with_notes(
        self,
        authorized_client: AsyncClient,
        test_tag: Tag,
        test_note,
    ):
        """Test deletion of tag with associated notes."""
        response = await authorized_client.delete(f"/api/v1/tags/{test_tag.id}")
        # Should succeed and remove association
        assert response.status_code == 204

    async def test_delete_tag_not_found(self, authorized_client: AsyncClient):
        """Test deletion of non-existent tag."""
        response = await authorized_client.delete(f"/api/v1/tags/{uuid4()}")
        assert response.status_code == 404

    async def test_delete_tag_unauthorized(self, client: AsyncClient, test_tag: Tag):
        """Test tag deletion without authentication."""
        response = await client.delete(f"/api/v1/tags/{test_tag.id}")
        assert response.status_code == 401


class TestTagsFilterNotes:
    """Tests for GET /api/v1/tags/{tag_id}/notes endpoint."""

    async def test_get_notes_by_tag_success(
        self,
        authorized_client: AsyncClient,
        test_tag: Tag,
        test_note,
    ):
        """Test getting notes filtered by tag."""
        response = await authorized_client.get(f"/api/v1/tags/{test_tag.id}/notes")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert any(n["id"] == str(test_note.id) for n in data["items"])

    async def test_get_notes_by_tag_not_found(self, authorized_client: AsyncClient):
        """Test getting notes for non-existent tag."""
        response = await authorized_client.get(f"/api/v1/tags/{uuid4()}/notes")
        assert response.status_code == 404

    async def test_get_notes_by_tag_pagination(
        self,
        authorized_client: AsyncClient,
        test_tag: Tag,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test pagination for notes by tag."""
        from app.models.note import Note
        
        # Create multiple notes with the tag
        for i in range(15):
            note = Note(
                title=f"Tagged Note {i}",
                content=f"Content {i}",
                user_id=test_user.id,
            )
            note.tags.append(test_tag)
            db_session.add(note)
        await db_session.commit()

        response = await authorized_client.get(
            f"/api/v1/tags/{test_tag.id}/notes?page=1&size=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] >= 15
