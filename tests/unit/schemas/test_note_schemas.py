"""Unit tests for Note Pydantic schemas validation."""
import pytest
from datetime import datetime
from uuid import uuid4

from app.schemas.note import (
    NoteCreate, NoteUpdate, NoteStatusUpdate,
    NoteResponse, NoteSummaryResponse, NoteSearchParams
)


class TestNoteCreate:
    """Tests for NoteCreate schema."""

    def test_create_valid(self):
        """Test valid note creation schema."""
        # Arrange & Act
        note = NoteCreate(
            title="Test Note",
            content="# Markdown Content",
            is_pinned=False
        )
        
        # Assert
        assert note.title == "Test Note"
        assert note.content == "# Markdown Content"

    def test_create_minimal(self):
        """Test minimal valid note creation."""
        # Arrange & Act
        note = NoteCreate(title="Minimal")
        
        # Assert
        assert note.title == "Minimal"
        assert note.content == ""
        assert note.is_pinned is False

    def test_create_title_too_short(self):
        """Test title must be at least 1 character."""
        # Act & Assert
        with pytest.raises(ValueError):
            NoteCreate(title="")

    def test_create_title_too_long(self):
        """Test title max length validation."""
        # Act & Assert
        with pytest.raises(ValueError):
            NoteCreate(title="x" * 201)

    @pytest.mark.parametrize("title", [
        "A",
        "Normal Title",
        "x" * 200,  # Max length
    ])
    def test_create_valid_title_lengths(self, title):
        """Test various valid title lengths."""
        # Act
        note = NoteCreate(title=title)
        
        # Assert
        assert note.title == title

    def test_create_with_tags(self):
        """Test note creation with tag IDs."""
        # Arrange
        tag_ids = [uuid4(), uuid4()]
        
        # Act
        note = NoteCreate(
            title="Tagged Note",
            tag_ids=tag_ids
        )
        
        # Assert
        assert note.tag_ids == tag_ids


class TestNoteUpdate:
    """Tests for NoteUpdate schema."""

    def test_update_all_fields(self):
        """Test updating all fields."""
        # Arrange & Act
        update = NoteUpdate(
            title="Updated Title",
            content="Updated content",
            category_id=uuid4(),
            tag_ids=[uuid4()]
        )
        
        # Assert
        assert update.title == "Updated Title"
        assert update.content == "Updated content"

    def test_update_partial(self):
        """Test partial update (some fields None)."""
        # Arrange & Act
        update = NoteUpdate(title="Only Title")
        
        # Assert
        assert update.title == "Only Title"
        assert update.content is None
        assert update.category_id is None

    def test_update_empty(self):
        """Test empty update (all fields None)."""
        # Arrange & Act
        update = NoteUpdate()
        
        # Assert
        assert update.title is None
        assert update.content is None


class TestNoteStatusUpdate:
    """Tests for NoteStatusUpdate schema."""

    def test_update_pinned(self):
        """Test updating pinned status."""
        # Arrange & Act
        update = NoteStatusUpdate(is_pinned=True)
        
        # Assert
        assert update.is_pinned is True
        assert update.is_archived is None

    def test_update_archived(self):
        """Test updating archived status."""
        # Arrange & Act
        update = NoteStatusUpdate(is_archived=True)
        
        # Assert
        assert update.is_archived is True
        assert update.is_pinned is None

    def test_update_both(self):
        """Test updating both statuses."""
        # Arrange & Act
        update = NoteStatusUpdate(is_pinned=False, is_archived=True)
        
        # Assert
        assert update.is_pinned is False
        assert update.is_archived is True


class TestNoteSearchParams:
    """Tests for NoteSearchParams schema."""

    def test_search_defaults(self):
        """Test default search parameters."""
        # Arrange & Act
        params = NoteSearchParams()
        
        # Assert
        assert params.q is None
        assert params.is_archived is False
        assert params.limit == 20
        assert params.sort_by == "updated_at"
        assert params.sort_order == "desc"

    def test_search_custom_limit(self):
        """Test custom limit within bounds."""
        # Arrange & Act
        params = NoteSearchParams(limit=50)
        
        # Assert
        assert params.limit == 50

    def test_search_limit_min_bound(self):
        """Test limit minimum boundary."""
        # Act & Assert
        with pytest.raises(ValueError):
            NoteSearchParams(limit=0)

    def test_search_limit_max_bound(self):
        """Test limit maximum boundary."""
        # Act & Assert
        with pytest.raises(ValueError):
            NoteSearchParams(limit=101)

    @pytest.mark.parametrize("sort_by", ["created_at", "updated_at", "title"])
    def test_search_valid_sort_by(self, sort_by):
        """Test valid sort_by values."""
        # Act
        params = NoteSearchParams(sort_by=sort_by)
        
        # Assert
        assert params.sort_by == sort_by

    def test_search_invalid_sort_by(self):
        """Test invalid sort_by value."""
        # Act & Assert
        with pytest.raises(ValueError):
            NoteSearchParams(sort_by="invalid_field")

    @pytest.mark.parametrize("sort_order", ["asc", "desc"])
    def test_search_valid_sort_order(self, sort_order):
        """Test valid sort_order values."""
        # Act
        params = NoteSearchParams(sort_order=sort_order)
        
        # Assert
        assert params.sort_order == sort_order

    def test_search_invalid_sort_order(self):
        """Test invalid sort_order value."""
        # Act & Assert
        with pytest.raises(ValueError):
            NoteSearchParams(sort_order="invalid")

    def test_search_with_query(self):
        """Test search with query string."""
        # Arrange & Act
        params = NoteSearchParams(q="test query")
        
        # Assert
        assert params.q == "test query"

    def test_search_with_category(self):
        """Test search with category filter."""
        # Arrange
        cat_id = uuid4()
        
        # Act
        params = NoteSearchParams(category_id=cat_id)
        
        # Assert
        assert params.category_id == cat_id

    def test_search_with_tags(self):
        """Test search with tag filters."""
        # Arrange
        tag_ids = [uuid4(), uuid4()]
        
        # Act
        params = NoteSearchParams(tag_ids=tag_ids)
        
        # Assert
        assert params.tag_ids == tag_ids

    def test_search_with_date_range(self):
        """Test search with date range filters."""
        # Arrange
        after = datetime(2024, 1, 1)
        before = datetime(2024, 12, 31)
        
        # Act
        params = NoteSearchParams(
            created_after=after,
            created_before=before
        )
        
        # Assert
        assert params.created_after == after
        assert params.created_before == before
