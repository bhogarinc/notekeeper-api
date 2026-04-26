"""Fixtures and configuration for integration tests."""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.note import Note, Category, Tag
from app.core.security import create_access_token, get_password_hash

# Test database URL
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    settings.POSTGRES_DB, f"{settings.POSTGRES_DB}_test"
)

# Create async engine for tests
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator:
    """Create test database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
        # Clean up test data
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with overridden dependencies."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession) -> User:
    """Create a test superuser."""
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_token(test_user: User) -> str:
    """Generate access token for test user."""
    return create_access_token(subject=test_user.id)


@pytest_asyncio.fixture
async def superuser_token(test_superuser: User) -> str:
    """Generate access token for test superuser."""
    return create_access_token(subject=test_superuser.id)


@pytest_asyncio.fixture
async def authorized_client(client: AsyncClient, user_token: str) -> AsyncClient:
    """Create an authorized client with valid token."""
    client.headers["Authorization"] = f"Bearer {user_token}"
    return client


@pytest_asyncio.fixture
async def test_category(db_session: AsyncSession, test_user: User) -> Category:
    """Create a test category."""
    category = Category(
        name="Test Category",
        description="Test category description",
        user_id=test_user.id,
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest_asyncio.fixture
async def test_tag(db_session: AsyncSession, test_user: User) -> Tag:
    """Create a test tag."""
    tag = Tag(
        name="test-tag",
        color="#FF5733",
        user_id=test_user.id,
    )
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)
    return tag


@pytest_asyncio.fixture
async def test_note(
    db_session: AsyncSession, 
    test_user: User, 
    test_category: Category,
    test_tag: Tag
) -> Note:
    """Create a test note with category and tag."""
    note = Note(
        title="Test Note",
        content="This is a test note content with **markdown** support.",
        user_id=test_user.id,
        category_id=test_category.id,
        is_pinned=False,
        is_archived=False,
    )
    note.tags.append(test_tag)
    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)
    return note


@pytest_asyncio.fixture
async def multiple_notes(db_session: AsyncSession, test_user: User) -> list[Note]:
    """Create multiple test notes for pagination testing."""
    notes = []
    for i in range(25):
        note = Note(
            title=f"Test Note {i}",
            content=f"Content for note {i}",
            user_id=test_user.id,
            is_pinned=i < 3,
            is_archived=i >= 20,
        )
        db_session.add(note)
        notes.append(note)
    await db_session.commit()
    for note in notes:
        await db_session.refresh(note)
    return notes


@pytest.fixture
def expired_token() -> str:
    """Generate an expired JWT token."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    
    now = datetime.now(timezone.utc)
    expire = now - timedelta(minutes=10)
    to_encode = {"exp": expire, "sub": "test-user-id"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
