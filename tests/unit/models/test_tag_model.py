"""Unit tests for Tag model business logic."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.models.tag import Tag


class TestTagNoteCount:
    """Tests for Tag.note_count property."""

    def test_note_count_zero(self):
        """Test note count for tag with no notes."""
        # Arrange
        tag = Tag(user_id=uuid4(), name="empty-tag", color="#6366f1")
        tag.notes = MagicMock()
        tag.notes.count.return_value = 0
        
        # Act
        result = tag.note_count
        
        # Assert
        assert result == 0

    def test_note_count_multiple(self):
        """Test note count for tag with multiple notes."""
        # Arrange
        tag = Tag(user_id=uuid4(), name="popular", color="#10b981")
        tag.notes = MagicMock()
        tag.notes.count.return_value = 5
        
        # Act
        result = tag.note_count
        
        # Assert
        assert result == 5

    def test_note_count_calls_count_method(self):
        """Test that note_count calls the underlying count method."""
        # Arrange
        tag = Tag(user_id=uuid4(), name="test", color="#f59e0b")
        tag.notes = MagicMock()
        
        # Act
        _ = tag.note_count
        
        # Assert
        tag.notes.count.assert_called_once()


class TestTagRepr:
    """Tests for Tag string representation."""

    def test_repr_contains_name(self):
        """Test repr includes tag name."""
        # Arrange
        tag = Tag(user_id=uuid4(), name="important", color="#6366f1")
        
        # Act
        result = repr(tag)
        
        # Assert
        assert "important" in result

    def test_repr_contains_id(self):
        """Test repr includes tag ID."""
        # Arrange
        tag = Tag(user_id=uuid4(), name="test", color="#10b981")
        
        # Act
        result = repr(tag)
        
        # Assert
        assert str(tag.id) in result

    def test_repr_contains_user_id(self):
        """Test repr includes user ID."""
        # Arrange
        user_id = uuid4()
        tag = Tag(user_id=user_id, name="personal", color="#f59e0b")
        
        # Act
        result = repr(tag)
        
        # Assert
        assert str(user_id) in result


class TestTagDefaultColor:
    """Tests for Tag default color."""

    def test_default_color(self):
        """Test default color is set on creation."""
        # Arrange & Act
        tag = Tag(user_id=uuid4(), name="no-color")
        
        # Assert
        assert tag.color == "#10b981"

    def test_custom_color(self):
        """Test custom color can be set."""
        # Arrange & Act
        tag = Tag(user_id=uuid4(), name="custom", color="#ff5733")
        
        # Assert
        assert tag.color == "#ff5733"
