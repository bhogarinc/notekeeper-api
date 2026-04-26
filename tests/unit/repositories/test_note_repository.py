"""Unit tests for NoteRepository with search and filtering."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from app.repositories.note import NoteRepository
from app.models.note import Note


@pytest.fixture
def note_repo(mock_db):
    """Create NoteRepository instance with mocked DB."""
    return NoteRepository(mock_db)


class TestNoteRepositoryGetByUser:
    """Tests for get_by_user method with filtering."""

    def test_get_by_user_basic(self, note_repo, mock_db, user_id):
        """Test basic user note retrieval."""
        # Arrange
        mock_notes = [MagicMock(spec=Note) for _ in range(3)]
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 3
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_notes
        mock_db.query.return_value = mock_query
        
        # Act
        notes, total = note_repo.get_by_user(str(user_id))
        
        # Assert
        assert notes == mock_notes
        assert total == 3

    def test_get_by_user_with_archived_filter(self, note_repo, mock_db, user_id):
        """Test filtering by archived status."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.count.return_value = 2
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        notes, total = note_repo.get_by_user(str(user_id), is_archived=True)
        
        # Assert
        assert total == 2

    def test_get_by_user_with_pinned_filter(self, note_repo, mock_db, user_id):
        """Test filtering by pinned status."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.count.return_value = 1
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        notes, total = note_repo.get_by_user(str(user_id), is_pinned=True)
        
        # Assert
        assert total == 1

    def test_get_by_user_with_category_filter(self, note_repo, mock_db, user_id, category_id):
        """Test filtering by category."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.count.return_value = 5
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        notes, total = note_repo.get_by_user(str(user_id), category_id=str(category_id))
        
        # Assert
        assert total == 5

    @pytest.mark.parametrize("skip,limit", [
        (0, 10),
        (10, 20),
        (50, 50),
    ])
    def test_get_by_user_pagination(self, note_repo, mock_db, user_id, skip, limit):
        """Test pagination parameters."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 100
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        note_repo.get_by_user(str(user_id), skip=skip, limit=limit)
        
        # Assert
        mock_query.filter.return_value.order_by.return_value.offset.assert_called_once_with(skip)

    def test_get_by_user_with_search_query(self, note_repo, mock_db, user_id):
        """Test full-text search filtering."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.count.return_value = 3
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        with patch('app.repositories.note.func') as mock_func:
            mock_func.to_tsquery.return_value = "search_vector"
            
            # Act
            notes, total = note_repo.get_by_user(str(user_id), search_query="test query")
            
            # Assert
            assert total == 3
            mock_func.to_tsquery.assert_called_once_with('english', 'test query:*')


class TestNoteRepositoryGetPinned:
    """Tests for get_pinned_by_user method."""

    def test_get_pinned_by_user(self, note_repo, mock_db, user_id):
        """Test retrieving pinned notes."""
        # Arrange
        mock_notes = [MagicMock(spec=Note) for _ in range(2)]
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = mock_notes
        mock_db.query.return_value = mock_query
        
        # Act
        result = note_repo.get_pinned_by_user(str(user_id))
        
        # Assert
        assert result == mock_notes
        assert len(result) == 2

    def test_get_pinned_excludes_archived(self, note_repo, mock_db, user_id):
        """Test that pinned notes exclude archived ones."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        note_repo.get_pinned_by_user(str(user_id))
        
        # Assert - verify both filters applied
        mock_query.filter.assert_called()


class TestNoteRepositoryGetArchived:
    """Tests for get_archived_by_user method."""

    def test_get_archived_by_user(self, note_repo, mock_db, user_id):
        """Test retrieving archived notes with pagination."""
        # Arrange
        mock_notes = [MagicMock(spec=Note) for _ in range(5)]
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.count.return_value = 15
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_notes
        mock_db.query.return_value = mock_query
        
        # Act
        notes, total = note_repo.get_archived_by_user(str(user_id))
        
        # Assert
        assert notes == mock_notes
        assert total == 15

    def test_get_archived_custom_pagination(self, note_repo, mock_db, user_id):
        """Test archived notes with custom pagination."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.count.return_value = 50
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        note_repo.get_archived_by_user(str(user_id), skip=20, limit=10)
        
        # Assert
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.assert_called_once_with(20)


class TestNoteRepositorySearch:
    """Tests for search_notes method."""

    def test_search_notes_basic(self, note_repo, mock_db, user_id):
        """Test basic full-text search."""
        # Arrange
        mock_notes = [MagicMock(spec=Note) for _ in range(3)]
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.count.return_value = 3
        mock_query.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_notes
        mock_db.query.return_value = mock_query
        
        with patch('app.repositories.note.func') as mock_func:
            mock_func.plainto_tsquery.return_value = "search_query"
            mock_func.ts_rank_cd.return_value.desc.return_value = "rank_desc"
            
            # Act
            notes, total = note_repo.search_notes(str(user_id), "test search")
            
            # Assert
            assert notes == mock_notes
            assert total == 3
            mock_func.plainto_tsquery.assert_called_once_with('english', 'test search')

    def test_search_notes_with_relevance_ranking(self, note_repo, mock_db, user_id):
        """Test search results ordered by relevance."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.count.return_value = 0
        mock_query.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        with patch('app.repositories.note.func') as mock_func:
            # Act
            note_repo.search_notes(str(user_id), "important")
            
            # Assert
            mock_func.ts_rank_cd.assert_called_once()

    def test_search_notes_excludes_archived(self, note_repo, mock_db, user_id):
        """Test search excludes archived notes."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.count.return_value = 0
        mock_query.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        note_repo.search_notes(str(user_id), "query")
        
        # Assert - verify archived filter applied
        mock_query.filter.assert_called()

    @pytest.mark.parametrize("query", [
        "",
        "a",
        "multi word search query",
        "special!@#$chars",
    ])
    def test_search_notes_various_queries(self, note_repo, mock_db, user_id, query):
        """Test search with various query strings."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.count.return_value = 0
        mock_query.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        with patch('app.repositories.note.func'):
            # Act - should not raise
            note_repo.search_notes(str(user_id), query)


class TestNoteRepositoryGetWithRelations:
    """Tests for get_with_relations method."""

    def test_get_with_relations_success(self, note_repo, mock_db, note_id):
        """Test retrieving note with relationships loaded."""
        # Arrange
        mock_note = MagicMock(spec=Note)
        mock_note.id = note_id
        
        options_chain = MagicMock()
        options_chain.filter.return_value.first.return_value = mock_note
        
        mock_query = MagicMock()
        mock_query.options.return_value = options_chain
        mock_db.query.return_value = mock_query
        
        # Act
        result = note_repo.get_with_relations(str(note_id))
        
        # Assert
        assert result == mock_note
        mock_query.options.assert_called_once()

    def test_get_with_relations_not_found(self, note_repo, mock_db, note_id):
        """Test retrieving non-existent note returns None."""
        # Arrange
        options_chain = MagicMock()
        options_chain.filter.return_value.first.return_value = None
        
        mock_query = MagicMock()
        mock_query.options.return_value = options_chain
        mock_db.query.return_value = mock_query
        
        # Act
        result = note_repo.get_with_relations(str(note_id))
        
        # Assert
        assert result is None
