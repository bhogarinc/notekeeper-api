"""Pytest fixtures and test configuration."""
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from unittest.mock import MagicMock, create_autospec
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.note import Note, NoteVersion
from app.models.category import Category
from app.models.tag import Tag
from app.schemas.note import NoteCreate, NoteUpdate


@pytest.fixture
def mock_db():
    """Create a mocked SQLAlchemy session."""
    db = MagicMock(spec=Session)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.rollback = MagicMock()
    db.query = MagicMock(return_value=MagicMock())
    return db


@pytest.fixture
def user_id():
    """Generate a consistent user UUID."""
    return UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture
def note_id():
    """Generate a consistent note UUID."""
    return UUID("87654321-4321-4321-4321-cba987654321")


@pytest.fixture
def category_id():
    """Generate a consistent category UUID."""
    return UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def tag_id():
    """Generate a consistent tag UUID."""
    return UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def test_user(user_id):
    """Create a test user instance."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = "test@example.com"
    user.username = "testuser"
    user.password_hash = "hashed_password"
    user.is_active = True
    user.is_verified = True
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = None
    user.notes = MagicMock()
    user.categories = MagicMock()
    user.tags = MagicMock()
    return user


@pytest.fixture
def test_note(note_id, user_id, category_id):
    """Create a test note instance."""
    note = MagicMock(spec=Note)
    note.id = note_id
    note.user_id = user_id
    note.category_id = category_id
    note.title = "Test Note Title"
    note.content = "# Test Content\n\nThis is test content."
    note.content_html = "<h1>Test Content</h1><p>This is test content.</p>"
    note.is_pinned = False
    note.is_archived = False
    note.pinned_at = None
    note.archived_at = None
    note.color = "#6366f1"
    note.version = 1
    note.search_vector = None
    note.tags = []
    note.created_at = datetime.utcnow()
    note.updated_at = datetime.utcnow()
    return note


@pytest.fixture
def test_pinned_note(note_id, user_id):
    """Create a test pinned note instance."""
    note = MagicMock(spec=Note)
    note.id = note_id
    note.user_id = user_id
    note.category_id = None
    note.title = "Pinned Note"
    note.content = "Pinned content"
    note.is_pinned = True
    note.is_archived = False
    note.pinned_at = datetime.utcnow()
    note.archived_at = None
    note.tags = []
    note.version = 1
    return note


@pytest.fixture
def test_archived_note(note_id, user_id):
    """Create a test archived note instance."""
    note = MagicMock(spec=Note)
    note.id = note_id
    note.user_id = user_id
    note.category_id = None
    note.title = "Archived Note"
    note.content = "Archived content"
    note.is_pinned = False
    note.is_archived = True
    note.pinned_at = None
    note.archived_at = datetime.utcnow()
    note.tags = []
    note.version = 1
    return note


@pytest.fixture
def test_category(category_id, user_id):
    """Create a test category instance."""
    category = MagicMock(spec=Category)
    category.id = category_id
    category.user_id = user_id
    category.name = "Test Category"
    category.color = "#10b981"
    category.icon = "folder"
    category.parent_id = None
    category.notes = MagicMock()
    category.children = []
    return category


@pytest.fixture
def test_tag(tag_id, user_id):
    """Create a test tag instance."""
    tag = MagicMock(spec=Tag)
    tag.id = tag_id
    tag.user_id = user_id
    tag.name = "test-tag"
    tag.color = "#f59e0b"
    tag.notes = MagicMock()
    return tag


@pytest.fixture
def note_create_data():
    """Create valid NoteCreate schema data."""
    return NoteCreate(
        title="New Note Title",
        content="# New Content",
        category_id=None,
        tag_ids=[],
        is_pinned=False
    )


@pytest.fixture
def note_update_data():
    """Create valid NoteUpdate schema data."""
    return NoteUpdate(
        title="Updated Title",
        content="Updated content",
        category_id=None,
        tag_ids=[]
    )


@pytest.fixture
def note_create_factory():
    """Factory for creating NoteCreate variations."""
    def _create(
        title: str = "Default Title",
        content: str = "Default content",
        category_id: UUID = None,
        tag_ids: list = None,
        is_pinned: bool = False,
        color: str = "#6366f1"
    ):
        return NoteCreate(
            title=title,
            content=content,
            category_id=category_id,
            tag_ids=tag_ids or [],
            is_pinned=is_pinned
        )
    return _create


@pytest.fixture
def note_factory(user_id):
    """Factory for creating Note mock instances."""
    def _create(
        note_id: UUID = None,
        title: str = "Factory Note",
        content: str = "Factory content",
        is_pinned: bool = False,
        is_archived: bool = False,
        category_id: UUID = None
    ):
        note = MagicMock(spec=Note)
        note.id = note_id or uuid4()
        note.user_id = user_id
        note.title = title
        note.content = content
        note.is_pinned = is_pinned
        note.is_archived = is_archived
        note.category_id = category_id
        note.tags = []
        note.version = 1
        note.pinned_at = datetime.utcnow() if is_pinned else None
        note.archived_at = datetime.utcnow() if is_archived else None
        return note
    return _create
