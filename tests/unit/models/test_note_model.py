"""Unit tests for Note model business logic."""
import pytest
from datetime import datetime
from uuid import uuid4

from app.models.note import Note


class TestNotePin:
    """Tests for Note.pin method."""

    def test_pin_sets_pinned_true(self):
        """Test pinning sets is_pinned to True."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        note.is_pinned = False
        
        # Act
        note.pin()
        
        # Assert
        assert note.is_pinned is True

    def test_pin_sets_pinned_at_timestamp(self):
        """Test pinning sets pinned_at timestamp."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        note.pinned_at = None
        
        # Act
        note.pin()
        
        # Assert
        assert note.pinned_at is not None
        assert isinstance(note.pinned_at, datetime)

    def test_pin_already_pinned_updates_timestamp(self):
        """Test re-pinning updates timestamp."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        old_time = datetime.utcnow() - timedelta(hours=1)
        note.pinned_at = old_time
        
        # Act
        note.pin()
        
        # Assert
        assert note.pinned_at > old_time


class TestNoteUnpin:
    """Tests for Note.unpin method."""

    def test_unpin_sets_pinned_false(self):
        """Test unpinning sets is_pinned to False."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        note.is_pinned = True
        note.pinned_at = datetime.utcnow()
        
        # Act
        note.unpin()
        
        # Assert
        assert note.is_pinned is False

    def test_unpin_clears_pinned_at(self):
        """Test unpinning clears pinned_at timestamp."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        note.is_pinned = True
        note.pinned_at = datetime.utcnow()
        
        # Act
        note.unpin()
        
        # Assert
        assert note.pinned_at is None

    def test_unpin_already_unpinned(self):
        """Test unpinning already unpinned note."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        note.is_pinned = False
        note.pinned_at = None
        
        # Act - should not raise
        note.unpin()
        
        # Assert
        assert note.is_pinned is False
        assert note.pinned_at is None


class TestNoteArchive:
    """Tests for Note.archive method."""

    def test_archive_sets_archived_true(self):
        """Test archiving sets is_archived to True."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        note.is_archived = False
        
        # Act
        note.archive()
        
        # Assert
        assert note.is_archived is True

    def test_archive_sets_archived_at_timestamp(self):
        """Test archiving sets archived_at timestamp."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        
        # Act
        note.archive()
        
        # Assert
        assert note.archived_at is not None
        assert isinstance(note.archived_at, datetime)


class TestNoteUnarchive:
    """Tests for Note.unarchive method."""

    def test_unarchive_sets_archived_false(self):
        """Test unarchiving sets is_archived to False."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        note.is_archived = True
        note.archived_at = datetime.utcnow()
        
        # Act
        note.unarchive()
        
        # Assert
        assert note.is_archived is False

    def test_unarchive_clears_archived_at(self):
        """Test unarchiving clears archived_at timestamp."""
        # Arrange
        note = Note(user_id=uuid4(), title="Test", content="Content")
        note.is_archived = True
        note.archived_at = datetime.utcnow()
        
        # Act
        note.unarchive()
        
        # Assert
        assert note.archived_at is None


class TestNoteRepr:
    """Tests for Note string representation."""

    def test_repr_contains_title(self):
        """Test repr includes note title."""
        # Arrange
        note = Note(user_id=uuid4(), title="My Test Note", content="Content")
        
        # Act
        result = repr(note)
        
        # Assert
        assert "My Test Note" in result

    def test_repr_truncates_long_title(self):
        """Test repr truncates titles over 50 chars."""
        # Arrange
        long_title = "A" * 100
        note = Note(user_id=uuid4(), title=long_title, content="Content")
        
        # Act
        result = repr(note)
        
        # Assert
        assert len(result) < 150  # Should be truncated


# Import timedelta for tests
from datetime import timedelta
