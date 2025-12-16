import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, status
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.injections import get_session
from app.main import create_app
from app.models import DbModel, UserModel, RideModel

# Use a separate file DB for pending tests (async driver)
DB_PATH = os.path.join(os.path.dirname(__file__), "pending_tests.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

@pytest_asyncio.fixture(scope="function")
async def app() -> FastAPI:
    application = create_app()
    if hasattr(application, "other_asgi_app"):
        return application.other_asgi_app
    return application

@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    
    async with engine.begin() as conn:
        await conn.run_sync(DbModel.metadata.drop_all)
        await conn.run_sync(DbModel.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_client(app: FastAPI, session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def test_user(session: AsyncSession) -> UserModel:
    user = UserModel(username="testuser", password="testpassword")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def test_ride(session: AsyncSession, test_user: UserModel) -> RideModel:
    ride = RideModel(
        code="ABC123",
        title="Test Ride",
        description="Test description",
        start_time=datetime(2025, 11, 18, 15, 30, tzinfo=timezone.utc),
        created_by_user_id=test_user.id,
    )
    session.add(ride)
    await session.commit()
    await session.refresh(ride)
    return ride

@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_client: AsyncClient, session: AsyncSession) -> dict[str, str]:
    user = UserModel(username="auth_user", password="authpassword")
    session.add(user)
    await session.commit()

    login_payload = {
        "username": "auth_user",
        "password": "authpassword",
    }
    response = await test_client.post("/auth/login", data=login_payload)
    assert response.status_code == status.HTTP_200_OK
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
