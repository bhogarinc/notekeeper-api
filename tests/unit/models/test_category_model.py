"""Unit tests for Category model business logic."""
import pytest
from uuid import uuid4

from app.models.category import Category


class TestCategoryGetFullPath:
    """Tests for Category.get_full_path method."""

    def test_get_full_path_root_category(self):
        """Test path for root category (no parent)."""
        # Arrange
        category = Category(
            user_id=uuid4(),
            name="Root Category",
            color="#6366f1"
        )
        category.parent = None
        
        # Act
        result = category.get_full_path()
        
        # Assert
        assert result == "Root Category"

    def test_get_full_path_with_parent(self):
        """Test path for category with parent."""
        # Arrange
        parent = Category(
            user_id=uuid4(),
            name="Parent",
            color="#6366f1"
        )
        child = Category(
            user_id=uuid4(),
            name="Child",
            color="#10b981",
            parent_id=parent.id
        )
        child.parent = parent
        parent.children = [child]
        
        # Act
        result = child.get_full_path()
        
        # Assert
        assert result == "Parent / Child"

    def test_get_full_path_deep_nesting(self):
        """Test path for deeply nested category."""
        # Arrange
        grandparent = Category(user_id=uuid4(), name="Grandparent", color="#6366f1")
        parent = Category(user_id=uuid4(), name="Parent", color="#10b981", parent_id=grandparent.id)
        child = Category(user_id=uuid4(), name="Child", color="#f59e0b", parent_id=parent.id)
        
        grandparent.children = [parent]
        parent.parent = grandparent
        parent.children = [child]
        child.parent = parent
        
        # Act
        result = child.get_full_path()
        
        # Assert
        assert result == "Grandparent / Parent / Child"


class TestCategoryGetDescendants:
    """Tests for Category.get_descendants method."""

    def test_get_descendants_no_children(self):
        """Test descendants for leaf category."""
        # Arrange
        category = Category(user_id=uuid4(), name="Leaf", color="#6366f1")
        category.children = []
        
        # Act
        result = category.get_descendants()
        
        # Assert
        assert result == []

    def test_get_descendants_direct_children(self):
        """Test descendants with only direct children."""
        # Arrange
        parent = Category(user_id=uuid4(), name="Parent", color="#6366f1")
        child1 = Category(user_id=uuid4(), name="Child1", color="#10b981", parent_id=parent.id)
        child2 = Category(user_id=uuid4(), name="Child2", color="#f59e0b", parent_id=parent.id)
        
        parent.children = [child1, child2]
        child1.children = []
        child2.children = []
        
        # Act
        result = parent.get_descendants()
        
        # Assert
        assert len(result) == 2
        assert child1 in result
        assert child2 in result

    def test_get_descendants_recursive(self):
        """Test recursive descendant retrieval."""
        # Arrange
        grandparent = Category(user_id=uuid4(), name="Grandparent", color="#6366f1")
        parent = Category(user_id=uuid4(), name="Parent", color="#10b981", parent_id=grandparent.id)
        child = Category(user_id=uuid4(), name="Child", color="#f59e0b", parent_id=parent.id)
        
        grandparent.children = [parent]
        parent.children = [child]
        child.children = []
        
        # Act
        result = grandparent.get_descendants()
        
        # Assert
        assert len(result) == 2
        assert parent in result
        assert child in result


class TestCategoryRepr:
    """Tests for Category string representation."""

    def test_repr_contains_name(self):
        """Test repr includes category name."""
        # Arrange
        category = Category(user_id=uuid4(), name="My Category", color="#6366f1")
        
        # Act
        result = repr(category)
        
        # Assert
        assert "My Category" in result

    def test_repr_contains_id(self):
        """Test repr includes category ID."""
        # Arrange
        category = Category(user_id=uuid4(), name="Test", color="#6366f1")
        
        # Act
        result = repr(category)
        
        # Assert
        assert str(category.id) in result
