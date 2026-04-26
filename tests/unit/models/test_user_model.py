"""Unit tests for User model business logic."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.models.user import User


class TestUserIsLocked:
    """Tests for User.is_locked method."""

    def test_is_locked_no_lock(self):
        """Test user with no lock is not locked."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.locked_until = None
        
        # Act
        result = user.is_locked()
        
        # Assert
        assert result is False

    def test_is_locked_past_timestamp(self):
        """Test user with past lock timestamp is not locked."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.locked_until = datetime.utcnow() - timedelta(minutes=5)
        
        # Act
        result = user.is_locked()
        
        # Assert
        assert result is False

    def test_is_locked_future_timestamp(self):
        """Test user with future lock timestamp is locked."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        # Act
        result = user.is_locked()
        
        # Assert
        assert result is True


class TestUserIncrementFailedLogin:
    """Tests for User.increment_failed_login method."""

    def test_increment_failed_login_increments_counter(self):
        """Test failed login attempts counter increments."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.failed_login_attempts = 2
        
        # Act
        user.increment_failed_login()
        
        # Assert
        assert user.failed_login_attempts == 3

    def test_increment_failed_login_locks_at_threshold(self):
        """Test account locks after 5 failed attempts."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.failed_login_attempts = 4
        
        # Act
        user.increment_failed_login()
        
        # Assert
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None
        assert user.locked_until > datetime.utcnow()

    def test_increment_failed_login_locks_after_threshold(self):
        """Test account remains locked beyond threshold."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.failed_login_attempts = 10
        
        # Act
        user.increment_failed_login()
        
        # Assert
        assert user.failed_login_attempts == 11
        assert user.locked_until is not None

    @pytest.mark.parametrize("initial_count", [0, 1, 2, 3, 4])
    def test_increment_various_counts(self, initial_count):
        """Test increment at various failure counts."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.failed_login_attempts = initial_count
        
        # Act
        user.increment_failed_login()
        
        # Assert
        assert user.failed_login_attempts == initial_count + 1


class TestUserResetFailedLogin:
    """Tests for User.reset_failed_login method."""

    def test_reset_clears_attempts(self):
        """Test reset clears failed attempts counter."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.failed_login_attempts = 5
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        # Act
        user.reset_failed_login()
        
        # Assert
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    def test_reset_sets_last_login(self):
        """Test reset updates last login timestamp."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.last_login = None
        
        # Act
        user.reset_failed_login()
        
        # Assert
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)

    def test_reset_already_cleared(self):
        """Test reset on already cleared state."""
        # Arrange
        user = User(email="test@test.com", username="test", password_hash="hash")
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Act - should not raise
        user.reset_failed_login()
        
        # Assert
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


class TestUserRepr:
    """Tests for User string representation."""

    def test_repr_contains_username(self):
        """Test repr includes username."""
        # Arrange
        user = User(email="test@test.com", username="testuser", password_hash="hash")
        
        # Act
        result = repr(user)
        
        # Assert
        assert "testuser" in result
        assert "test@test.com" in result
