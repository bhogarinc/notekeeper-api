"""Unit tests for NoteService business logic."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, create_autospec
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.services.note import NoteService
from app.models.note import Note, NoteVersion
from app.models.tag import Tag
from app.schemas.note import NoteCreate, NoteUpdate


@pytest.fixture
def note_service(mock_db):
    """Create NoteService instance with mocked DB."""
    return NoteService(mock_db)


@pytest.fixture(autouse=True)
def mock_markdown():
    """Mock markdown rendering."""
    with patch('app.services.note.markdown.markdown') as mock_md:
        mock_md.return_value = '<h1>Test</h1><p>Content</p>'
        yield mock_md


@pytest.fixture(autouse=True)
def mock_bleach():
    """Mock HTML sanitization."""
    with patch('app.services.note.clean') as mock_clean:
        mock_clean.return_value = '<h1>Test</h1><p>Content</p>'
        yield mock_clean


class TestNoteServiceCreate:
    """Tests for NoteService.create_note method."""

    def test_create_note_success(self, note_service, mock_db, user_id, note_create_data):
        """Test successful note creation."""
        # Arrange
        mock_note = MagicMock(spec=Note)
        mock_note.id = uuid4()
        mock_note.title = note_create_data.title
        mock_note.tags = []
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with patch.object(note_service.repository, 'create', return_value=mock_note):
            # Act
            result = note_service.create_note(str(user_id), note_create_data)
            
            # Assert
            assert result == mock_note
            note_service.repository.create.assert_called_once()

    def test_create_note_empty_title_sets_untitled(self, note_service, mock_db, user_id):
        """Test that empty title defaults to 'Untitled Note'."""
        # Arrange
        note_data = NoteCreate(title="", content="Content")
        mock_note = MagicMock(spec=Note)
        mock_note.id = uuid4()
        mock_note.tags = []
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with patch.object(note_service.repository, 'create', return_value=mock_note):
            # Act
            note_service.create_note(str(user_id), note_data)
            
            # Assert
            call_args = note_service.repository.create.call_args[0][0]
            assert call_args["title"] == "Untitled Note"

    def test_create_note_title_too_long_raises_error(self, note_service, user_id):
        """Test that title > 200 characters raises HTTPException."""
        # Arrange
        note_data = NoteCreate(title="x" * 201, content="Content")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            note_service.create_note(str(user_id), note_data)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "less than 200 characters" in exc_info.value.detail

    @pytest.mark.parametrize("title", ["", "   ", "\t\n"])
    def test_create_note_whitespace_title_defaults_to_untitled(
        self, note_service, mock_db, user_id, title
    ):
        """Test that whitespace-only titles default to 'Untitled Note'."""
        # Arrange
        note_data = NoteCreate(title=title, content="Content")
        mock_note = MagicMock(spec=Note)
        mock_note.tags = []
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with patch.object(note_service.repository, 'create', return_value=mock_note):
            # Act
            note_service.create_note(str(user_id), note_data)
            
            # Assert
            call_args = note_service.repository.create.call_args[0][0]
            assert call_args["title"] == "Untitled Note"

    def test_create_note_with_tags(self, note_service, mock_db, user_id, tag_id):
        """Test note creation with tag attachments."""
        # Arrange
        note_data = NoteCreate(
            title="Tagged Note",
            content="Content",
            tag_ids=[tag_id]
        )
        mock_note = MagicMock(spec=Note)
        mock_note.id = uuid4()
        mock_note.tags = []
        
        mock_tag = MagicMock(spec=Tag)
        mock_tag.id = tag_id
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_tag]
        
        with patch.object(note_service.repository, 'create', return_value=mock_note):
            # Act
            result = note_service.create_note(str(user_id), note_data)
            
            # Assert
            assert result == mock_note

    def test_create_note_renders_markdown(self, note_service, mock_db, user_id, mock_markdown):
        """Test that markdown content is rendered to HTML."""
        # Arrange
        note_data = NoteCreate(title="MD Note", content="# Heading")
        mock_note = MagicMock(spec=Note)
        mock_note.tags = []
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with patch.object(note_service.repository, 'create', return_value=mock_note):
            # Act
            note_service.create_note(str(user_id), note_data)
            
            # Assert
            mock_markdown.assert_called_once_with("# Heading", extensions=['fenced_code', 'tables'])


class TestNoteServiceUpdate:
    """Tests for NoteService.update_note method."""

    def test_update_note_success(self, note_service, mock_db, user_id, note_id, test_note):
        """Test successful note update."""
        # Arrange
        note_service.repository.get_by_id = MagicMock(return_value=test_note)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        update_data = NoteUpdate(title="Updated", content="New content")
        
        with patch.object(note_service.repository, 'update', return_value=test_note):
            # Act
            result = note_service.update_note(str(user_id), str(note_id), update_data)
            
            # Assert
            assert result == test_note

    def test_update_note_not_found_raises_404(self, note_service, user_id, note_id):
        """Test updating non-existent note raises 404."""
        # Arrange
        note_service.repository.get_by_id = MagicMock(return_value=None)
        update_data = NoteUpdate(title="Updated")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            note_service.update_note(str(user_id), str(note_id), update_data)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_update_note_wrong_user_raises_404(self, note_service, user_id, note_id):
        """Test updating another user's note raises 404."""
        # Arrange
        wrong_user_id = uuid4()
        mock_note = MagicMock(spec=Note)
        mock_note.user_id = wrong_user_id
        
        note_service.repository.get_by_id = MagicMock(return_value=mock_note)
        update_data = NoteUpdate(title="Updated")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            note_service.update_note(str(user_id), str(note_id), update_data)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_update_note_creates_version(self, note_service, mock_db, user_id, note_id, test_note):
        """Test that update creates a version backup."""
        # Arrange
        note_service.repository.get_by_id = MagicMock(return_value=test_note)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        update_data = NoteUpdate(title="Updated")
        
        with patch.object(note_service.repository, 'update', return_value=test_note):
            # Act
            note_service.update_note(str(user_id), str(note_id), update_data)
            
            # Assert
            mock_db.add.assert_called()
            call_args = mock_db.add.call_args[0][0]
            assert isinstance(call_args, NoteVersion)

    def test_update_note_title_too_long_raises_error(self, note_service, user_id, note_id, test_note):
        """Test that updated title > 200 characters raises error."""
        # Arrange
        note_service.repository.get_by_id = MagicMock(return_value=test_note)
        update_data = NoteUpdate(title="x" * 201)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            note_service.update_note(str(user_id), str(note_id), update_data)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_note_partial_fields(self, note_service, mock_db, user_id, note_id, test_note):
        """Test updating only specific fields leaves others unchanged."""
        # Arrange
        note_service.repository.get_by_id = MagicMock(return_value=test_note)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        update_data = NoteUpdate(title="Only Title Updated")
        
        with patch.object(note_service.repository, 'update', return_value=test_note) as mock_update:
            # Act
            note_service.update_note(str(user_id), str(note_id), update_data)
            
            # Assert
            call_args = mock_update.call_args[0][1]
            assert "title" in call_args
            assert "content" not in call_args


class TestNoteServiceDelete:
    """Tests for NoteService.delete_note method."""

    def test_delete_note_success(self, note_service, mock_db, user_id, note_id, test_note):
        """Test successful note deletion."""
        # Arrange
        note_service.repository.get_by_id = MagicMock(return_value=test_note)
        
        with patch.object(note_service.repository, 'delete') as mock_delete:
            # Act
            note_service.delete_note(str(user_id), str(note_id))
            
            # Assert
            mock_delete.assert_called_once_with(test_note)

    def test_delete_note_not_found_raises_404(self, note_service, user_id, note_id):
        """Test deleting non-existent note raises 404."""
        # Arrange
        note_service.repository.get_by_id = MagicMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            note_service.delete_note(str(user_id), str(note_id))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_note_wrong_user_raises_404(self, note_service, user_id, note_id):
        """Test deleting another user's note raises 404."""
        # Arrange
        wrong_user_id = uuid4()
        mock_note = MagicMock(spec=Note)
        mock_note.user_id = wrong_user_id
        
        note_service.repository.get_by_id = MagicMock(return_value=mock_note)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            note_service.delete_note(str(user_id), str(note_id))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestNoteServicePin:
    """Tests for NoteService.pin_note method."""

    def test_pin_note_success(self, note_service, user_id, note_id, test_note):
        """Test successful note pinning."""
        # Arrange
        test_note.is_archived = False
        note_service.repository.get_by_id = MagicMock(return_value=test_note)
        
        with patch.object(note_service.repository, 'update', return_value=test_note) as mock_update:
            # Act
            result = note_service.pin_note(str(user_id), str(note_id))
            
            # Assert
            assert result == test_note
            call_args = mock_update.call_args[0][1]
            assert call_args["is_pinned"] is True
            assert "pinned_at" in call_args

    def test_pin_archived_note_raises_error(self, note_service, user_id, note_id, test_note):
        """Test pinning archived note raises error."""
        # Arrange
        test_note.is_archived = True
        note_service.repository.get_by_id = MagicMock(return_value=test_note)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            note_service.pin_note(str(user_id), str(note_id))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot pin archived notes" in exc_info.value.detail

    def test_pin_note_not_found_raises_404(self, note_service, user_id, note_id):
        """Test pinning non-existent note raises 404."""
        # Arrange
        note_service.repository.get_by_id = MagicMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            note_service.pin_note(str(user_id), str(note_id))
        
        assert exc_info.value.status_code == 404


class TestNoteServiceArchive:
    """Tests for NoteService.archive_note method."""

    def test_archive_note_success(self, note_service, user_id, note_id, test_note):
        """Test successful note archiving."""
        # Arrange
        test_note.is_pinned = True
        note_service.repository.get_by_id = MagicMock(return_value=test_note)
        
        with patch.object(note_service.repository, 'update', return_value=test_note) as mock_update:
            # Act
            result = note_service.archive_note(str(user_id), str(note_id))
            
            # Assert
            assert result == test_note
            call_args = mock_update.call_args[0][1]
            assert call_args["is_archived"] is True
            assert call_args["is_pinned"] is False
            assert call_args["pinned_at"] is None

    def test_archive_note_unpins_first(self, note_service, user_id, note_id, test_note):
        """Test that archiving unpins the note."""
        # Arrange
        test_note.is_pinned = True
        test_note.pinned_at = datetime.utcnow()
        note_service.repository.get_by_id = MagicMock(return_value=test_note)
        
        with patch.object(note_service.repository, 'update', return_value=test_note) as mock_update:
            # Act
            note_service.archive_note(str(user_id), str(note_id))
            
            # Assert
            call_args = mock_update.call_args[0][1]
            assert call_args["is_pinned"] is False
            assert call_args["pinned_at"] is None


class TestNoteServicePrivateMethods:
    """Tests for NoteService private helper methods."""

    def test_render_markdown(self, note_service, mock_markdown, mock_bleach):
        """Test markdown rendering with sanitization."""
        # Arrange
        content = "# Heading\n\nParagraph"
        
        # Act
        result = note_service._render_markdown(content)
        
        # Assert
        mock_markdown.assert_called_once_with(content, extensions=['fenced_code', 'tables'])
        mock_bleach.assert_called_once()

    def test_render_markdown_empty_content(self, note_service):
        """Test markdown rendering with empty content."""
        # Act
        result = note_service._render_markdown("")
        
        # Assert
        assert result == ""

    def test_update_search_vector(self, note_service, mock_db, test_note):
        """Test search vector update."""
        # Arrange
        with patch('app.services.note.func') as mock_func:
            mock_func.to_tsvector.return_value = "search_vector_value"
            
            # Act
            note_service._update_search_vector(test_note)
            
            # Assert
            mock_db.commit.assert_called_once()

    def test_create_version(self, note_service, mock_db, test_note):
        """Test version backup creation."""
        # Act
        note_service._create_version(test_note)
        
        # Assert
        mock_db.add.assert_called_once()
        added_obj = mock_db.add.call_args[0][0]
        assert isinstance(added_obj, NoteVersion)
        assert added_obj.note_id == test_note.id
        assert test_note.version == 2  # Incremented

    def test_attach_tags(self, note_service, mock_db, test_note, tag_id):
        """Test attaching tags to note."""
        # Arrange
        mock_tag = MagicMock(spec=Tag)
        mock_tag.id = tag_id
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_tag]
        test_note.tags = []
        
        # Act
        note_service._attach_tags(test_note, [tag_id])
        
        # Assert
        assert mock_tag in test_note.tags
        mock_db.commit.assert_called_once()

    def test_sync_tags_replaces_all(self, note_service, mock_db, test_note, tag_id):
        """Test that sync_tags replaces all existing tags."""
        # Arrange
        old_tag = MagicMock(spec=Tag)
        old_tag.id = uuid4()
        test_note.tags = [old_tag]
        
        new_tag = MagicMock(spec=Tag)
        new_tag.id = tag_id
        mock_db.query.return_value.filter.return_value.all.return_value = [new_tag]
        
        # Act
        note_service._sync_tags(test_note, [tag_id])
        
        # Assert
        assert old_tag not in test_note.tags
        assert new_tag in test_note.tags
        mock_db.commit.assert_called_once()
