"""
Configuration for integration tests with real database
Supports both SQLite (default) and PostgreSQL (for @pytest.mark.postgres tests)
"""
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.future import select
from sqlalchemy import text
from fastapi import FastAPI, status
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.models import DbModel, UserModel, RideModel, ParticipationModel
from app.injections import get_session

import tempfile

# Test database paths
# Use a temporary directory for the SQLite DB to avoid locking issues on mapped volumes (Docker/Windows)
TEST_DB_FILENAME = "test_integration.db"
TEMP_DIR = tempfile.gettempdir()
ABS_DB_PATH = os.path.join(TEMP_DIR, TEST_DB_FILENAME)

SQLITE_URL = f"sqlite+aiosqlite:///{ABS_DB_PATH}"
# Adjust Postgres URL for Docker service discovery if needed, but we focus on SQLite fix first
POSTGRES_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://saferide_user:MyPass2025vadim@127.0.0.1:5432/saferide_db")


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "postgres: tests that require PostgreSQL database"
    )


@pytest_asyncio.fixture(scope="session")
async def test_engine(request):
    """Create test database engine (SQLite or PostgreSQL based on marker)"""
    # Check if we're running postgres tests
    use_postgres = request.config.getoption("-m") == "postgres"
    
    if use_postgres:
        # PostgreSQL
        engine = create_async_engine(POSTGRES_URL)
        print("\n(SUCCESS) Using PostgreSQL for tests")
    else:
        # SQLite (default)
        if os.path.exists(ABS_DB_PATH):
            try:
                os.remove(ABS_DB_PATH)
            except OSError:
                pass
        
        # Use NullPool to avoid file locking issues with SQLite
        engine = create_async_engine(
            SQLITE_URL,
            connect_args={"check_same_thread": False},
            poolclass=NullPool
        )
        print("\n(INFO) Using SQLite for tests with NullPool")
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(DbModel.metadata.create_all)
    
    yield engine
    
    await engine.dispose()
    
    if not use_postgres:
        # Remove SQLite database after engine is disposed
        try:
            if os.path.exists(ABS_DB_PATH):
                os.remove(ABS_DB_PATH)
        except PermissionError:
            pass  # File might still be in use


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine):
    """Create a fresh database session for each test"""
    TestingSessionLocal = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine):
    """Create a fresh database session for each test"""
    
    # NUCLEAR OPTION: Drop and Recreate tables to guarantee clean state
    # This is slightly slower but avoids all IntegrityError/Locking non-sense with SQLite
    async with test_engine.begin() as conn:
        await conn.run_sync(DbModel.metadata.drop_all)
        await conn.run_sync(DbModel.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(test_db):
    """Create test client with overridden database dependency"""
    app = create_app()
    if hasattr(app, "other_asgi_app"):
        app = app.other_asgi_app
    
    async def override_get_session():
        # STRATEGY #1: Mimic the behavior of the real get_session,
        # but use the session from the test_db fixture.
        # Use begin_nested() or just begin() if the session is not yet in a transaction.
        # In SQLAlchemy 2.0+, the session usually starts a transaction on first use.
        if not test_db.in_transaction():
            async with test_db.begin():
                yield test_db
        else:
            async with test_db.begin_nested():
                yield test_db
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client):
    """Create a test user and return authentication headers"""
    # Create user
    user_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = await client.post("/users/", json=user_data)
    assert response.status_code == 201
    
    # Login
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_user_headers(client):
    """Create a second test user and return authentication headers"""
    # Create user
    user_data = {
        "username": "testuser2",
        "password": "testpass456"
    }
    
    response = await client.post("/users/", json=user_data)
    assert response.status_code == 201
    
    # Login
    login_data = {
        "username": "testuser2",
        "password": "testpass456"
    }
    
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
