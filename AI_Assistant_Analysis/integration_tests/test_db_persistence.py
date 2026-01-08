import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.repositories import UserRepository, RideRepository
from AI_Assistant_Analysis.integration_tests.conftest import SQLITE_URL

@pytest.mark.asyncio
async def test_api_persistence_across_sessions(client: AsyncClient):
    """
    Test that data created via the API is persisted and visible in a fresh DB session.
    This would have caught the missing commit() in injections.py.
    """
    username = "persistence_user"
    password = "testpassword"
    
    # 1. Create user via API
    response = await client.post(
        "/users/", 
        json={"username": username, "password": password}
    )
    assert response.status_code == 201
    
    # 2. Verify existence using a COMPLETELY DIFFERENT session object
    # pointing to the same test database
    engine = create_async_engine(SQLITE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with session_factory() as fresh_session:
        repo = UserRepository(session=fresh_session)
        user = await repo.get_by_username(username=username)
        
        assert user is not None, "User should be persisted in DB and visible to a new session"
        assert user.username == username
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_ride_persistence_across_sessions(client: AsyncClient, auth_headers):
    """Test that rides are persisted correctly across sessions"""
    ride_data = {
        "title": "Persistence Ride",
        "description": "Checks if commit works",
        "start_time": "2025-12-24T10:00:00"
    }
    
    # 1. Create ride via API
    response = await client.post("/rides/", json=ride_data, headers=auth_headers)
    assert response.status_code == 201
    ride_id = response.json()["id"]
    
    # 2. Verify in a fresh session
    engine = create_async_engine(SQLITE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with session_factory() as fresh_session:
        repo = RideRepository(session=fresh_session)
        ride = await repo.get_by_id(ride_id=ride_id)
        
        assert ride is not None, "Ride should be persisted in DB"
        assert ride.title == "Persistence Ride"
    
    await engine.dispose()
