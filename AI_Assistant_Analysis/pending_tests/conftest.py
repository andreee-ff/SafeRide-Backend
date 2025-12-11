from collections.abc import Generator, Callable

from datetime import datetime, timezone
import secrets, string
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

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
    # Ensure tests use SQLite, overriding any local .env configuration
    db_path = os.path.join(os.path.dirname(__file__), "pending_tests.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    application = create_app()
    if hasattr(application, "other_asgi_app"):
         return application.other_asgi_app
    return application

@fixture(scope="function")
def session(app: FastAPI) -> Generator[Session]:
    # Use a separate DB for pending tests
    db_path = os.path.join(os.path.dirname(__file__), "pending_tests.db")
    engine = create_engine(f"sqlite:///{db_path}")
    DbModel.metadata.create_all(bind=engine)
    try:
        session = Session(bind=engine)
        try:
            app.dependency_overrides[get_session] = lambda: session
            yield session
        finally:
            session.close()
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
