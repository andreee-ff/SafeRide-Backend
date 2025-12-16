import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator, Callable, Awaitable
from ipaddress import ip_address
from datetime import datetime, timezone
import secrets, string

from fastapi import FastAPI, status
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.injections import get_session
from app.main import create_app
from app.models import DbModel, UserModel, RideModel, ParticipationModel

# Используем файловую базу с NullPool для надежности в асинхронных тестах
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest_asyncio.fixture(scope="function")
async def app() -> FastAPI:
    application = create_app()
    if hasattr(application, "other_asgi_app"):
        return application.other_asgi_app
    return application

@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    # 1. Создаем движок
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    # 2. Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(DbModel.metadata.drop_all)
        await conn.run_sync(DbModel.metadata.create_all)

    # 3. Фабрика сессий
    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    # 4. Выдаем сессию
    async with TestingSessionLocal() as session:
        yield session
        # Откат изменений после теста
        await session.rollback()
    
    # 5. Закрываем движок
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_client(app: FastAPI, session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Переопределяем зависимость get_session
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

# ------------------ HELPER FIXTURES ------------------ #

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
async def test_participation(session: AsyncSession, test_user: UserModel, test_ride: RideModel) -> ParticipationModel:
    participation = ParticipationModel(
        user_id = test_user.id,
        ride_id = test_ride.id,
        latitude = 48.1351,
        longitude = 11.5820,
        updated_at = datetime(2025, 11, 18, 15, 30, tzinfo=timezone.utc),
    )
    session.add(participation)
    await session.commit()
    await session.refresh(participation)
    return participation

@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_client: AsyncClient, session: AsyncSession) -> dict[str, str]:
    # Создаем пользователя для логина
    username = "auth_user"
    password = "authpassword"
    user = UserModel(username=username, password=password)
    session.add(user)
    await session.commit()

    login_payload = {
        "username": username,
        "password": password,
    }
    response = await test_client.post("/auth/login", data=login_payload)
    assert response.status_code == status.HTTP_200_OK
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ------------------ RIDE FACTORY ------------------ #

# Тип для подсказки: теперь это асинхронная фабрика
RideFactoryType = Callable[..., Awaitable[RideModel]]

@pytest_asyncio.fixture(scope="function")
async def ride_factory(session: AsyncSession, test_user: UserModel) -> RideFactoryType:
    async def _create_ride(
            *,
            code: str | None = None,
            title: str = "Test Ride",
            description: str = "Test description",
            start_time: datetime | None = None,
    ) -> RideModel:
        random_code = "".join(secrets.choice(string.ascii_uppercase) for _ in range(6))
        ride = RideModel(
            code=code or random_code,
            title=f"{title} {random_code}",
            description=f"{description} {random_code}",
            start_time=start_time or datetime(2025, 11, 18, 15, 30, tzinfo=timezone.utc),
            created_by_user_id=test_user.id,
        )
        session.add(ride)
        await session.commit()
        await session.refresh(ride)
        return ride
    
    return _create_ride
