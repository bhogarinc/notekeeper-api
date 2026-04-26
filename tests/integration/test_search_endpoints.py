"""Integration tests for search endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note, Category, Tag
from app.models.user import User


class TestSearchNotes:
    """Tests for GET /api/v1/search endpoint."""

    async def test_search_notes_by_title(
        self,
        authorized_client: AsyncClient,
        test_note: Note,
    ):
        """Test searching notes by title."""
        response = await authorized_client.get("/api/v1/search?q=Test Note")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert any(n["id"] == str(test_note.id) for n in data["items"])

    async def test_search_notes_by_content(
        self,
        authorized_client: AsyncClient,
        test_note: Note,
    ):
        """Test searching notes by content."""
        response = await authorized_client.get("/api/v1/search?q=markdown")
        assert response.status_code == 200
        data = response.json()
        assert any(n["id"] == str(test_note.id) for n in data["items"])

    async def test_search_notes_no_results(
        self, authorized_client: AsyncClient
    ):
        """Test search with no matching results."""
        response = await authorized_client.get("/api/v1/search?q=xyznonexistent")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0

    async def test_search_notes_empty_query(
        self, authorized_client: AsyncClient
    ):
        """Test search with empty query."""
        response = await authorized_client.get("/api/v1/search?q=")
        assert response.status_code == 422

    async def test_search_notes_pagination(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test search results pagination."""
        # Create multiple searchable notes
        for i in range(15):
            note = Note(
                title=f"Searchable Note {i}",
                content=f"Content with searchable keyword {i}",
                user_id=test_user.id,
            )
            db_session.add(note)
        await db_session.commit()

        response = await authorized_client.get("/api/v1/search?q=searchable&page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["total"] >= 15

    async def test_search_notes_with_filters(
        self,
        authorized_client: AsyncClient,
        test_note: Note,
        test_category: Category,
    ):
        """Test search with additional filters."""
        response = await authorized_client.get(
            f"/api/v1/search?q=Test&category_id={test_category.id}"
        )
        assert response.status_code == 200
        data = response.json()
        # Should filter by both search query and category
        assert all(
            n.get("category_id") == str(test_category.id) for n in data["items"]
        )

    async def test_search_notes_sorting(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test search results sorting."""
        # Create notes with different dates
        for i in range(5):
            note = Note(
                title=f"Sortable Note {i}",
                content="Sortable content",
                user_id=test_user.id,
            )
            db_session.add(note)
        await db_session.commit()

        response = await authorized_client.get(
            "/api/v1/search?q=sortable&sort_by=created_at&order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        dates = [n["created_at"] for n in data["items"]]
        assert dates == sorted(dates, reverse=True)

    async def test_search_notes_unauthorized(self, client: AsyncClient):
        """Test search without authentication."""
        response = await client.get("/api/v1/search?q=test")
        assert response.status_code == 401

    async def test_search_notes_isolated_by_user(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that search only returns current user's notes."""
        from app.core.security import get_password_hash
        
        # Create another user with a note
        other_user = User(
            email="othersearch@example.com",
            username="othersearchuser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_note = Note(
            title="Other User Secret Note",
            content="Secret content",
            user_id=other_user.id,
        )
        db_session.add(other_note)
        await db_session.commit()

        # Search should not find other user's note
        response = await authorized_client.get("/api/v1/search?q=Secret")
        assert response.status_code == 200
        data = response.json()
        assert not any("Secret" in n["title"] for n in data["items"])


class TestAdvancedSearch:
    """Tests for advanced search features."""

    async def test_search_by_tag(
        self,
        authorized_client: AsyncClient,
        test_note: Note,
        test_tag: Tag,
    ):
        """Test searching notes by tag."""
        response = await authorized_client.get(f"/api/v1/search?tag={test_tag.name}")
        assert response.status_code == 200
        data = response.json()
        assert any(n["id"] == str(test_note.id) for n in data["items"])

    async def test_search_by_date_range(
        self,
        authorized_client: AsyncClient,
        test_note: Note,
    ):
        """Test searching notes by date range."""
        from datetime import datetime, timedelta, timezone
        
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=7)).isoformat()
        end_date = (now + timedelta(days=1)).isoformat()
        
        response = await authorized_client.get(
            f"/api/v1/search?q=Test&start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200

    async def test_search_combined_filters(
        self,
        authorized_client: AsyncClient,
        test_note: Note,
        test_category: Category,
        test_tag: Tag,
    ):
        """Test search with multiple combined filters."""
        response = await authorized_client.get(
            f"/api/v1/search?q=Test&category_id={test_category.id}&tag={test_tag.name}&is_pinned=false"
        )
        assert response.status_code == 200
        data = response.json()
        # Should match all criteria
        for note in data["items"]:
            assert note.get("category_id") == str(test_category.id)
            assert note.get("is_pinned") is False


class TestSearchSuggestions:
    """Tests for search suggestions/autocomplete."""

    async def test_search_suggestions(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test search suggestions endpoint."""
        # Create notes with similar titles
        for title in ["Python Tutorial", "Python Guide", "JavaScript Tips"]:
            note = Note(
                title=title,
                content="Content",
                user_id=test_user.id,
            )
            db_session.add(note)
        await db_session.commit()

        response = await authorized_client.get("/api/v1/search/suggestions?q=Pyt")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should suggest "Python Tutorial" and "Python Guide"
        assert any("Python" in s for s in data)

    async def test_search_suggestions_min_chars(
        self, authorized_client: AsyncClient
    ):
        """Test suggestions require minimum characters."""
        response = await authorized_client.get("/api/v1/search/suggestions?q=a")
        assert response.status_code == 422  # Too short

    async def test_search_suggestions_unauthorized(self, client: AsyncClient):
        """Test suggestions without authentication."""
        response = await client.get("/api/v1/search/suggestions?q=test")
        assert response.status_code == 401
