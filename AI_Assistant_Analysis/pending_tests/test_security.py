from datetime import datetime, timezone
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserModel, RideModel
from app.security import get_password_hash

@pytest.mark.asyncio
async def test_create_ride_requires_authentication(test_client: AsyncClient):
    """Verify that POST /rides/ returns 401 without token"""
    payload = {
        "title": "Unauthorized Ride",
        "description": "Should not be created",
        "start_time": "2025-12-01T10:00:00Z"
    }
    response = await test_client.post("/rides/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_only_creator_can_delete_ride(
    test_client: AsyncClient, 
    session: AsyncSession, 
):
    """Verify that only ride creator can delete it"""
    # 1. Create a user (victim) and their ride
    victim = UserModel(username="victim", password=get_password_hash("password"))
    session.add(victim)
    await session.commit()
    await session.refresh(victim)
    
    victim_ride = RideModel(
        code="VICTIM1",
        title="Victim Ride",
        created_by_user_id=victim.id,
        start_time=datetime(2025, 12, 1, 10, 0, 0, tzinfo=timezone.utc)
    )
    session.add(victim_ride)
    await session.commit()
    await session.refresh(victim_ride)
    
    # 2. Login as attacker
    attacker = UserModel(username="attacker", password=get_password_hash("password"))
    session.add(attacker)
    await session.commit()
    
    login_payload = {"username": "attacker", "password": "password"}
    login_response = await test_client.post("/auth/login", data=login_payload)
    attacker_token = login_response.json()["access_token"]
    attacker_headers = {"Authorization": f"Bearer {attacker_token}"}
    
    # 3. Attacker tries to delete victim's ride
    response = await test_client.delete(f"/rides/{victim_ride.id}", headers=attacker_headers)
    
    # Expect 403 Forbidden or 404 Not Found (depending on how your API handles ownership check vs existence)
    # Ideally 403 if it finds it but denies access, or 404 if it filters by user ownership first.
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

@pytest.mark.asyncio
async def test_invalid_jwt_format(test_client: AsyncClient):
    """Verify JWT format validation"""
    headers = {"Authorization": "Bearer invalid.token.format"}
    response = await test_client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
