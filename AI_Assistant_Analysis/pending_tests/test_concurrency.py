from fastapi import status
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserModel, RideModel
import secrets

@pytest.mark.asyncio
async def test_multiple_users_same_ride(
    test_client: AsyncClient, 
    session: AsyncSession, 
    test_ride: RideModel
):
    """Verify multiple users can participate in same ride"""
    # This is a functional test for multi-user participation.
    # True concurrency (race conditions) is hard to simulate with TestClient + SQLite.
    
    users_count = 5
    
    for i in range(users_count):
        # 1. Create unique user
        username = f"user_conc_{i}_{secrets.token_hex(4)}"
        password = "password"
        user = UserModel(username=username, password=password)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # 2. Login to get token
        login_payload = {"username": username, "password": password}
        login_response = await test_client.post("/auth/login", data=login_payload)
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Participate in ride
        part_payload = {
            "ride_code": test_ride.code,
            "latitude": 50.0 + i, # Just some diff values
            "longitude": 10.0 + i
        }
        part_response = await test_client.post("/participations/", json=part_payload, headers=headers)
        assert part_response.status_code == status.HTTP_201_CREATED

    assert True
