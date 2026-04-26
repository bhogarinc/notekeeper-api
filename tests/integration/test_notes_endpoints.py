"""Integration tests for notes endpoints."""
import pytest
import asyncio
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note, Category, Tag
from app.models.user import User


class TestNotesCreate:
    """Tests for POST /api/v1/notes endpoint."""

    async def test_create_note_success(
        self, authorized_client: AsyncClient, test_category: Category
    ):
        """Test successful note creation."""
        response = await authorized_client.post(
            "/api/v1/notes",
            json={
                "title": "New Integration Test Note",
                "content": "This is the **content** of the note.",
                "category_id": str(test_category.id),
                "is_pinned": True,
                "tags": ["integration", "test"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Integration Test Note"
        assert data["content"] == "This is the **content** of the note."
        assert data["category_id"] == str(test_category.id)
        assert data["is_pinned"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_note_minimal(self, authorized_client: AsyncClient):
        """Test note creation with minimal fields."""
        response = await authorized_client.post(
            "/api/v1/notes",
            json={
                "title": "Minimal Note",
                "content": "Minimal content",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Note"
        assert data["is_pinned"] is False
        assert data["is_archived"] is False

    async def test_create_note_unauthorized(self, client: AsyncClient):
        """Test note creation without authentication."""
        response = await client.post(
            "/api/v1/notes",
            json={"title": "Unauthorized Note", "content": "Content"},
        )
        assert response.status_code == 401

    async def test_create_note_expired_token(
        self, client: AsyncClient, expired_token: str
    ):
        """Test note creation with expired token."""
        response = await client.post(
            "/api/v1/notes",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={"title": "Expired Token Note", "content": "Content"},
        )
        assert response.status_code == 401

    @pytest.mark.parametrize(
        "payload,expected_status",
        [
            ({"content": "Missing title"}, 422),
            ({"title": ""}, 422),
            ({"title": "a" * 201}, 422),  # Title too long
            ({"title": "Valid", "content": "a" * 50001}, 422),  # Content too long
            ({"title": "Valid", "category_id": "invalid-uuid"}, 422),
        ],
    )
    async def test_create_note_validation(
        self, authorized_client: AsyncClient, payload: dict, expected_status: int
    ):
        """Test note creation validation errors."""
        response = await authorized_client.post("/api/v1/notes", json=payload)
        assert response.status_code == expected_status

    async def test_create_note_invalid_category(
        self, authorized_client: AsyncClient
    ):
        """Test note creation with non-existent category."""
        response = await authorized_client.post(
            "/api/v1/notes",
            json={
                "title": "Note with Bad Category",
                "content": "Content",
                "category_id": str(uuid4()),
            },
        )
        assert response.status_code == 404


class TestNotesList:
    """Tests for GET /api/v1/notes endpoint."""

    async def test_list_notes_success(
        self, authorized_client: AsyncClient, multiple_notes: list[Note]
    ):
        """Test successful notes listing."""
        response = await authorized_client.get("/api/v1/notes")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert len(data["items"]) <= 20  # Default page size

    async def test_list_notes_pagination(
        self, authorized_client: AsyncClient, multiple_notes: list[Note]
    ):
        """Test notes pagination."""
        # Test page 1
        response = await authorized_client.get("/api/v1/notes?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10
        assert len(data["items"]) == 10

        # Test page 2
        response = await authorized_client.get("/api/v1/notes?page=2&size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 10

    async def test_list_notes_filter_by_category(
        self,
        authorized_client: AsyncClient,
        test_note: Note,
        test_category: Category,
    ):
        """Test filtering notes by category."""
        response = await authorized_client.get(
            f"/api/v1/notes?category_id={test_category.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert all(n["category_id"] == str(test_category.id) for n in data["items"])

    async def test_list_notes_filter_by_tag(
        self, authorized_client: AsyncClient, test_note: Note, test_tag
    ):
        """Test filtering notes by tag."""
        response = await authorized_client.get(f"/api/v1/notes?tag={test_tag.name}")
        assert response.status_code == 200
        data = response.json()
        assert any(test_tag.name in n.get("tags", []) for n in data["items"])

    async def test_list_notes_filter_pinned(
        self, authorized_client: AsyncClient, multiple_notes: list[Note]
    ):
        """Test filtering pinned notes."""
        response = await authorized_client.get("/api/v1/notes?is_pinned=true")
        assert response.status_code == 200
        data = response.json()
        assert all(n["is_pinned"] is True for n in data["items"])

    async def test_list_notes_filter_archived(
        self, authorized_client: AsyncClient, multiple_notes: list[Note]
    ):
        """Test filtering archived notes."""
        response = await authorized_client.get("/api/v1/notes?is_archived=true")
        assert response.status_code == 200
        data = response.json()
        assert all(n["is_archived"] is True for n in data["items"])

    async def test_list_notes_search(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test full-text search in notes."""
        response = await authorized_client.get("/api/v1/notes?search=test")
        assert response.status_code == 200
        data = response.json()
        # Should find notes with "test" in title or content
        assert len(data["items"]) > 0

    async def test_list_notes_sorting(
        self, authorized_client: AsyncClient, multiple_notes: list[Note]
    ):
        """Test notes sorting."""
        # Sort by title ascending
        response = await authorized_client.get("/api/v1/notes?sort_by=title&order=asc")
        assert response.status_code == 200
        data = response.json()
        titles = [n["title"] for n in data["items"]]
        assert titles == sorted(titles)

        # Sort by created_at descending
        response = await authorized_client.get(
            "/api/v1/notes?sort_by=created_at&order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        dates = [n["created_at"] for n in data["items"]]
        assert dates == sorted(dates, reverse=True)

    async def test_list_notes_unauthorized(self, client: AsyncClient):
        """Test notes listing without authentication."""
        response = await client.get("/api/v1/notes")
        assert response.status_code == 401

    async def test_list_notes_invalid_pagination(
        self, authorized_client: AsyncClient
    ):
        """Test notes listing with invalid pagination params."""
        response = await authorized_client.get("/api/v1/notes?page=0")
        assert response.status_code == 422

        response = await authorized_client.get("/api/v1/notes?size=101")
        assert response.status_code == 422


class TestNotesGet:
    """Tests for GET /api/v1/notes/{note_id} endpoint."""

    async def test_get_note_success(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test successful note retrieval."""
        response = await authorized_client.get(f"/api/v1/notes/{test_note.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_note.id)
        assert data["title"] == test_note.title
        assert data["content"] == test_note.content
        assert "tags" in data
        assert "category" in data

    async def test_get_note_not_found(self, authorized_client: AsyncClient):
        """Test retrieval of non-existent note."""
        response = await authorized_client.get(f"/api/v1/notes/{uuid4()}")
        assert response.status_code == 404

    async def test_get_note_invalid_id(self, authorized_client: AsyncClient):
        """Test retrieval with invalid note ID."""
        response = await authorized_client.get("/api/v1/notes/invalid-uuid")
        assert response.status_code == 422

    async def test_get_note_other_users_note(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test retrieval of another user's note (should fail)."""
        # Create another user and their note
        from app.core.security import get_password_hash
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_note = Note(
            title="Other User's Note",
            content="Private content",
            user_id=other_user.id,
        )
        db_session.add(other_note)
        await db_session.commit()
        await db_session.refresh(other_note)

        response = await authorized_client.get(f"/api/v1/notes/{other_note.id}")
        assert response.status_code == 404  # Should not reveal existence

    async def test_get_note_unauthorized(self, client: AsyncClient, test_note: Note):
        """Test note retrieval without authentication."""
        response = await client.get(f"/api/v1/notes/{test_note.id}")
        assert response.status_code == 401


class TestNotesUpdate:
    """Tests for PUT /api/v1/notes/{note_id} endpoint."""

    async def test_update_note_success(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test successful note update."""
        response = await authorized_client.put(
            f"/api/v1/notes/{test_note.id}",
            json={
                "title": "Updated Title",
                "content": "Updated content",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content"
        assert data["updated_at"] != data["created_at"]

    async def test_update_note_partial(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test partial note update (PATCH behavior)."""
        original_title = test_note.title
        response = await authorized_client.put(
            f"/api/v1/notes/{test_note.id}",
            json={"content": "Only content updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == original_title
        assert data["content"] == "Only content updated"

    async def test_update_note_not_found(self, authorized_client: AsyncClient):
        """Test update of non-existent note."""
        response = await authorized_client.put(
            f"/api/v1/notes/{uuid4()}",
            json={"title": "Updated Title"},
        )
        assert response.status_code == 404

    async def test_update_note_validation_error(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test note update with invalid data."""
        response = await authorized_client.put(
            f"/api/v1/notes/{test_note.id}",
            json={"title": ""},
        )
        assert response.status_code == 422

    async def test_update_note_unauthorized(self, client: AsyncClient, test_note: Note):
        """Test note update without authentication."""
        response = await client.put(
            f"/api/v1/notes/{test_note.id}",
            json={"title": "Updated Title"},
        )
        assert response.status_code == 401


class TestNotesDelete:
    """Tests for DELETE /api/v1/notes/{note_id} endpoint."""

    async def test_delete_note_success(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test successful note deletion."""
        response = await authorized_client.delete(f"/api/v1/notes/{test_note.id}")
        assert response.status_code == 204

        # Verify note is deleted
        get_response = await authorized_client.get(f"/api/v1/notes/{test_note.id}")
        assert get_response.status_code == 404

    async def test_delete_note_not_found(self, authorized_client: AsyncClient):
        """Test deletion of non-existent note."""
        response = await authorized_client.delete(f"/api/v1/notes/{uuid4()}")
        assert response.status_code == 404

    async def test_delete_note_unauthorized(self, client: AsyncClient, test_note: Note):
        """Test note deletion without authentication."""
        response = await client.delete(f"/api/v1/notes/{test_note.id}")
        assert response.status_code == 401


class TestNotesPin:
    """Tests for PUT /api/v1/notes/{note_id}/pin endpoint."""

    async def test_pin_note_success(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test successful note pinning."""
        assert test_note.is_pinned is False
        
        response = await authorized_client.put(f"/api/v1/notes/{test_note.id}/pin")
        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] is True

    async def test_unpin_note_success(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test successful note unpinning."""
        # First pin the note
        await authorized_client.put(f"/api/v1/notes/{test_note.id}/pin")
        
        # Then unpin
        response = await authorized_client.put(f"/api/v1/notes/{test_note.id}/pin")
        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] is False

    async def test_pin_note_not_found(self, authorized_client: AsyncClient):
        """Test pinning non-existent note."""
        response = await authorized_client.put(f"/api/v1/notes/{uuid4()}/pin")
        assert response.status_code == 404


class TestNotesArchive:
    """Tests for PUT /api/v1/notes/{note_id}/archive endpoint."""

    async def test_archive_note_success(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test successful note archiving."""
        response = await authorized_client.put(
            f"/api/v1/notes/{test_note.id}/archive"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is True

    async def test_unarchive_note_success(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test successful note unarchiving."""
        # First archive
        await authorized_client.put(f"/api/v1/notes/{test_note.id}/archive")
        
        # Then unarchive
        response = await authorized_client.put(
            f"/api/v1/notes/{test_note.id}/archive"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is False

    async def test_archive_note_not_found(self, authorized_client: AsyncClient):
        """Test archiving non-existent note."""
        response = await authorized_client.put(f"/api/v1/notes/{uuid4()}/archive")
        assert response.status_code == 404


class TestNotesConcurrent:
    """Tests for concurrent note operations."""

    async def test_concurrent_note_updates(
        self, authorized_client: AsyncClient, test_note: Note
    ):
        """Test concurrent note updates."""
        async def update_note(title_suffix: str):
            return await authorized_client.put(
                f"/api/v1/notes/{test_note.id}",
                json={"title": f"Updated {title_suffix}"},
            )

        # Send concurrent updates
        responses = await asyncio.gather(
            update_note("1"),
            update_note("2"),
            update_note("3"),
        )
        
        # All should succeed (last write wins)
        assert all(r.status_code == 200 for r in responses)

    async def test_concurrent_note_creates(
        self, authorized_client: AsyncClient
    ):
        """Test concurrent note creation."""
        async def create_note(idx: int):
            return await authorized_client.post(
                "/api/v1/notes",
                json={
                    "title": f"Concurrent Note {idx}",
                    "content": f"Content {idx}",
                },
            )

        responses = await asyncio.gather(*[create_note(i) for i in range(10)])
        
        # All should succeed
        assert all(r.status_code == 201 for r in responses)
        
        # Verify all notes created
        list_response = await authorized_client.get("/api/v1/notes?size=100")
        data = list_response.json()
        assert data["total"] >= 10
