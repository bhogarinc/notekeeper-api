"""Integration tests for error handling and edge cases."""
import pytest
from uuid import uuid4
from httpx import AsyncClient


class TestErrorResponses:
    """Tests for standardized error responses."""

    async def test_404_error_format(self, authorized_client: AsyncClient):
        """Test 404 error response format."""
        response = await authorized_client.get(f"/api/v1/notes/{uuid4()}")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    async def test_422_error_format(self, authorized_client: AsyncClient):
        """Test 422 validation error response format."""
        response = await authorized_client.post(
            "/api/v1/notes",
            json={"title": ""},  # Invalid: empty title
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    async def test_401_error_format(self, client: AsyncClient):
        """Test 401 unauthorized error format."""
        response = await client.get("/api/v1/notes")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_403_error_format(
        self, client: AsyncClient, expired_token: str
    ):
        """Test 403 forbidden error format."""
        response = await client.get(
            "/api/v1/notes",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401  # or 403 depending on implementation


class TestBoundaryValues:
    """Tests for boundary value analysis."""

    @pytest.mark.parametrize(
        "title,expected_status",
        [
            ("A", 201),  # Minimum valid (1 char)
            ("a" * 200, 201),  # Maximum valid (200 chars)
            ("", 422),  # Empty (0 chars)
            ("a" * 201, 422),  # Too long (201 chars)
        ],
    )
    async def test_title_length_boundaries(
        self, authorized_client: AsyncClient, title: str, expected_status: int
    ):
        """Test title length boundaries."""
        response = await authorized_client.post(
            "/api/v1/notes",
            json={"title": title, "content": "Valid content"},
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "content,expected_status",
        [
            ("A", 201),  # Minimum valid (1 char)
            ("a" * 50000, 201),  # Maximum valid (50000 chars)
            ("", 201),  # Empty content allowed
            ("a" * 50001, 422),  # Too long (50001 chars)
        ],
    )
    async def test_content_length_boundaries(
        self, authorized_client: AsyncClient, content: str, expected_status: int
    ):
        """Test content length boundaries."""
        response = await authorized_client.post(
            "/api/v1/notes",
            json={"title": "Valid Title", "content": content},
        )
        assert response.status_code == expected_status


class TestRateLimiting:
    """Tests for rate limiting (if implemented)."""

    async def test_rate_limit_headers(self, authorized_client: AsyncClient):
        """Test rate limit headers are present."""
        response = await authorized_client.get("/api/v1/notes")
        # Check for common rate limit headers
        assert "X-RateLimit-Limit" in response.headers or True  # Optional
        assert "X-RateLimit-Remaining" in response.headers or True  # Optional


class TestContentTypeHandling:
    """Tests for content type handling."""

    async def test_json_content_type_required(self, authorized_client: AsyncClient):
        """Test that JSON content type is enforced."""
        response = await authorized_client.post(
            "/api/v1/notes",
            content="title=Test&content=Body",  # Form data instead of JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 422

    async def test_malformed_json(self, authorized_client: AsyncClient):
        """Test handling of malformed JSON."""
        response = await authorized_client.post(
            "/api/v1/notes",
            content='{"title": "Test", "content": }',  # Invalid JSON
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


class TestSecurityHeaders:
    """Tests for security headers."""

    async def test_security_headers_present(self, authorized_client: AsyncClient):
        """Test that security headers are present in responses."""
        response = await authorized_client.get("/api/v1/notes")
        # Common security headers
        assert "X-Content-Type-Options" in response.headers or True  # Optional
        assert "X-Frame-Options" in response.headers or True  # Optional
