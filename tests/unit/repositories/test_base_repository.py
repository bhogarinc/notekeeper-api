"""Unit tests for BaseRepository CRUD operations."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, create_autospec
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.repositories.base import BaseRepository
from app.models.base import Base, UUIDMixin, TimestampMixin


class TestModel(Base, UUIDMixin, TimestampMixin):
    """Test model for repository testing."""
    __tablename__ = "test_models"
    name: str = "test"


@pytest.fixture
def mock_db():
    """Create mocked SQLAlchemy session."""
    db = MagicMock(spec=Session)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.rollback = MagicMock()
    db.query = MagicMock(return_value=MagicMock())
    return db


@pytest.fixture
def base_repo(mock_db):
    """Create BaseRepository instance with mocked DB."""
    return BaseRepository(TestModel, mock_db)


class TestBaseRepositoryGetById:
    """Tests for get_by_id method."""

    def test_get_by_id_success(self, base_repo, mock_db):
        """Test successful retrieval by ID."""
        # Arrange
        test_id = uuid4()
        mock_entity = MagicMock(spec=TestModel)
        mock_entity.id = test_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_entity
        
        # Act
        result = base_repo.get_by_id(test_id)
        
        # Assert
        assert result == mock_entity

    def test_get_by_id_not_found_returns_none(self, base_repo, mock_db):
        """Test get_by_id returns None for non-existent ID."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = base_repo.get_by_id(uuid4())
        
        # Assert
        assert result is None


class TestBaseRepositoryGetByIdOr404:
    """Tests for get_by_id_or_404 method."""

    def test_get_by_id_or_404_success(self, base_repo, mock_db):
        """Test successful retrieval or 404."""
        # Arrange
        test_id = uuid4()
        mock_entity = MagicMock(spec=TestModel)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_entity
        
        # Act
        result = base_repo.get_by_id_or_404(test_id)
        
        # Assert
        assert result == mock_entity

    def test_get_by_id_or_404_not_found_raises(self, base_repo, mock_db):
        """Test 404 raised for non-existent entity."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            base_repo.get_by_id_or_404(uuid4())
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestBaseRepositoryGetAll:
    """Tests for get_all method."""

    def test_get_all_default_pagination(self, base_repo, mock_db):
        """Test default pagination parameters."""
        # Arrange
        mock_entities = [MagicMock(spec=TestModel) for _ in range(5)]
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_entities
        mock_db.query.return_value = mock_query
        
        # Act
        result = base_repo.get_all()
        
        # Assert
        assert result == mock_entities
        mock_query.offset.assert_called_once_with(0)
        mock_query.offset.return_value.limit.assert_called_once_with(100)

    def test_get_all_with_custom_pagination(self, base_repo, mock_db):
        """Test custom skip and limit parameters."""
        # Arrange
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        base_repo.get_all(skip=10, limit=20)
        
        # Assert
        mock_query.offset.assert_called_once_with(10)
        mock_query.offset.return_value.limit.assert_called_once_with(20)

    def test_get_all_with_ordering_desc(self, base_repo, mock_db):
        """Test descending order by field."""
        # Arrange
        mock_query = MagicMock()
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        base_repo.get_all(order_by="created_at", order_desc=True)
        
        # Assert
        mock_query.order_by.assert_called_once()


class TestBaseRepositoryCreate:
    """Tests for create method."""

    def test_create_success(self, base_repo, mock_db):
        """Test successful entity creation."""
        # Arrange
        data = {"name": "Test Entity"}
        
        # Act
        result = base_repo.create(data)
        
        # Assert
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_rollback_on_error(self, base_repo, mock_db):
        """Test rollback on SQLAlchemy error."""
        # Arrange
        data = {"name": "Test Entity"}
        mock_db.commit.side_effect = SQLAlchemyError("DB Error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            base_repo.create(data)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        mock_db.rollback.assert_called_once()

    @pytest.mark.parametrize("data", [
        {},
        {"name": ""},
        {"name": "x" * 1000},
    ])
    def test_create_various_data(self, base_repo, mock_db, data):
        """Test creation with various data inputs."""
        # Act
        result = base_repo.create(data)
        
        # Assert
        assert result is not None


class TestBaseRepositoryUpdate:
    """Tests for update method."""

    def test_update_success(self, base_repo, mock_db):
        """Test successful entity update."""
        # Arrange
        mock_entity = MagicMock(spec=TestModel)
        mock_entity.name = "Old Name"
        update_data = {"name": "New Name"}
        
        # Act
        result = base_repo.update(mock_entity, update_data)
        
        # Assert
        assert result == mock_entity
        assert mock_entity.name == "New Name"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_partial_fields(self, base_repo, mock_db):
        """Test updating only specified fields."""
        # Arrange
        mock_entity = MagicMock(spec=TestModel)
        mock_entity.name = "Original"
        mock_entity.other_field = "Keep This"
        update_data = {"name": "Updated"}
        
        # Act
        base_repo.update(mock_entity, update_data)
        
        # Assert
        assert mock_entity.name == "Updated"

    def test_update_rollback_on_error(self, base_repo, mock_db):
        """Test rollback on update error."""
        # Arrange
        mock_entity = MagicMock(spec=TestModel)
        mock_db.commit.side_effect = SQLAlchemyError("Update Error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            base_repo.update(mock_entity, {"name": "New"})
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        mock_db.rollback.assert_called_once()

    def test_update_invalid_field_ignored(self, base_repo, mock_db):
        """Test that invalid fields are ignored during update."""
        # Arrange
        mock_entity = MagicMock(spec=TestModel)
        mock_entity.name = "Test"
        update_data = {"name": "New", "nonexistent_field": "Ignored"}
        
        # Act
        base_repo.update(mock_entity, update_data)
        
        # Assert - should not raise error
        mock_db.commit.assert_called_once()


class TestBaseRepositoryDelete:
    """Tests for delete method."""

    def test_delete_success(self, base_repo, mock_db):
        """Test successful entity deletion."""
        # Arrange
        mock_entity = MagicMock(spec=TestModel)
        
        # Act
        base_repo.delete(mock_entity)
        
        # Assert
        mock_db.delete.assert_called_once_with(mock_entity)
        mock_db.commit.assert_called_once()

    def test_delete_rollback_on_error(self, base_repo, mock_db):
        """Test rollback on delete error."""
        # Arrange
        mock_entity = MagicMock(spec=TestModel)
        mock_db.commit.side_effect = SQLAlchemyError("Delete Error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            base_repo.delete(mock_entity)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        mock_db.rollback.assert_called_once()


class TestBaseRepositoryCount:
    """Tests for count method."""

    def test_count_all(self, base_repo, mock_db):
        """Test counting all entities."""
        # Arrange
        mock_scalar = MagicMock()
        mock_scalar.scalar.return_value = 42
        mock_db.query.return_value = mock_scalar
        
        # Act
        result = base_repo.count()
        
        # Assert
        assert result == 42

    def test_count_with_filters(self, base_repo, mock_db):
        """Test counting with filter criteria."""
        # Arrange
        mock_scalar = MagicMock()
        mock_scalar.filter.return_value.scalar.return_value = 10
        mock_db.query.return_value = mock_scalar
        
        # Act
        result = base_repo.count(name="Test")
        
        # Assert
        assert result == 10
