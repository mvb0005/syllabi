"""Pytest configuration and shared fixtures for the backend test suite."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.database import get_db
from backend.main import app
from backend.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an in-memory SQLite engine for the test session."""
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Return an async HTTP test client with the DB overridden."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
