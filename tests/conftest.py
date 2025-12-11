from collections.abc import Generator, Callable

from datetime import datetime, timezone
import secrets, string

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pytest import fixture
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.injections import get_session
from app.main import create_app
from app.models import DbModel, UserModel, RideModel, ParticipationModel

@fixture(scope="function")
def app() -> FastAPI:
    application = create_app()
    if hasattr(application, "other_asgi_app"):
        return application.other_asgi_app
    return application

@fixture(scope="function")
def session(app: FastAPI) -> Generator[Session]:
    engine = create_engine("sqlite:///test.db")
    DbModel.metadata.create_all(bind=engine)
    try:
        with (session := Session(bind=engine)).begin():
            app.dependency_overrides[get_session] = lambda: session
            yield session
            session.rollback()
    finally:
        DbModel.metadata.drop_all(engine)
        engine.dispose()

@fixture(scope="function")
def test_client(app: FastAPI, session: Session) -> Generator[TestClient]:
    with TestClient(app=app) as test_client:
        yield test_client

@fixture(scope="function")
def test_user(session: Session) -> UserModel:
    user = UserModel(username="testuser", password="testpassword")
    session.add(user)
    session.flush()
    return user



@fixture(scope="function")
def test_ride(session: Session, test_user: UserModel) -> RideModel:
    ride = RideModel(
        code="ABC123",
        title="Test Ride",
        description="Test description",
        start_time=datetime(2025, 11, 18, 15, 30, tzinfo=timezone.utc),
        created_by_user_id=test_user.id,
    )
    session.add(ride)
    session.flush()
    return ride

# ------------------ RIDE _ FACTORY
RideFactoryType = Callable[..., RideModel]

@fixture(scope="function")
def ride_factory(session: Session, test_user: UserModel) -> RideFactoryType:
    def _create_ride(
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
        session.flush()
        return ride
    
    return _create_ride


@fixture(scope="function")
def auth_headers(test_client: TestClient, session: Session,) -> dict[str, str]:
    user = UserModel(username="auth_user", password="authpassword")
    session.add(user)
    session.flush()

    login_payload = {
        "username": user.username,
        "password": user.password,
    }
    login_response = test_client.post("/auth/login", data=login_payload)
    assert login_response.status_code == status.HTTP_200_OK, login_response.text

    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}



# ------------------ PARTICIPATION
@fixture(scope="function")
def test_participation(
    session: Session,
    test_user: UserModel,
    test_ride: RideModel,
) -> ParticipationModel:
    participation = ParticipationModel(
        user_id = test_user.id,
        ride_id = test_ride.id,
        latitude = 48.1351,
        longitude = 11.5820,
        updated_at = datetime(2025, 11, 18, 15, 30, tzinfo=timezone.utc),
    )
    session.add(participation)
    session.flush()
    return participation
