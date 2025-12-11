"""
Configuration for integration tests with real database
Supports both SQLite (default) and PostgreSQL (for @pytest.mark.postgres tests)
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import DbModel
from app.injections import get_session

# Test database paths
TEST_DB_PATH = "test_integration.db"
SQLITE_URL = f"sqlite:///./{TEST_DB_PATH}"
POSTGRES_URL = "postgresql://saferide_user:MyPass2025vadim@127.0.0.1:5432/saferide_db"


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "postgres: tests that require PostgreSQL database"
    )


@pytest.fixture(scope="session")
def test_engine(request):
    """Create test database engine (SQLite or PostgreSQL based on marker)"""
    # Check if we're running postgres tests
    use_postgres = request.config.getoption("-m") == "postgres"
    
    if use_postgres:
        # PostgreSQL
        engine = create_engine(POSTGRES_URL)
        print("\n(SUCCESS) Using PostgreSQL for tests")
    else:
        # SQLite (default)
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        
        engine = create_engine(
            SQLITE_URL,
            connect_args={"check_same_thread": False}
        )
        print("\n(INFO) Using SQLite for tests")
    
    # Create all tables
    DbModel.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    if use_postgres:
        # Clear PostgreSQL tables
        DbModel.metadata.drop_all(bind=engine)
    
    engine.dispose()
    
    if not use_postgres:
        # Remove SQLite database after engine is disposed
        import time
        time.sleep(0.1)  # Give Windows time to release the file
        try:
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
        except PermissionError:
            pass  # File might still be in use, will be cleaned up next run


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a fresh database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    session = TestingSessionLocal()
    
    yield session
    
    # Rollback and close session after each test
    session.rollback()
    session.close()
    
    # Clear all tables
    for table in reversed(DbModel.metadata.sorted_tables):
        session.execute(table.delete())
        session.commit()


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with overridden database dependency"""
    app = create_app()
    # If application is a socketio.ASGIApp, we need the underlying FastAPI app
    if hasattr(app, "other_asgi_app"):
        app = app.other_asgi_app
    
    def override_get_session():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Create a test user and return authentication headers"""
    # Create user
    user_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    
    # Login
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers(client):
    """Create a second test user and return authentication headers"""
    # Create user
    user_data = {
        "username": "testuser2",
        "password": "testpass456"
    }
    
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    
    # Login
    login_data = {
        "username": "testuser2",
        "password": "testpass456"
    }
    
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
