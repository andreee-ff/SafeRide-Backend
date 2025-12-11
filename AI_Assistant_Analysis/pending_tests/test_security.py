from datetime import datetime, timezone
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import UserModel, RideModel

def test_create_ride_requires_authentication(test_client: TestClient):
    """Verify that POST /rides/ returns 401 without token"""
    payload = {
        "title": "Unauthorized Ride",
        "description": "Should not be created",
        "start_time": "2025-12-01T10:00:00Z"
    }
    response = test_client.post("/rides/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_only_creator_can_delete_ride(
    test_client: TestClient, 
    session: Session, 
):
    """Verify that only ride creator can delete it"""
    # 1. Create a user (victim) and their ride
    victim = UserModel(username="victim", password="password")
    session.add(victim)
    session.flush()
    
    victim_ride = RideModel(
        code="VICTIM1",
        title="Victim Ride",
        created_by_user_id=victim.id,
        start_time=datetime(2025, 12, 1, 10, 0, 0, tzinfo=timezone.utc)
    )
    session.add(victim_ride)
    session.commit()
    
    # 2. Login as attacker
    attacker = UserModel(username="attacker", password="password")
    session.add(attacker)
    session.commit()
    
    login_payload = {"username": "attacker", "password": "password"}
    login_response = test_client.post("/auth/login", data=login_payload)
    attacker_token = login_response.json()["access_token"]
    attacker_headers = {"Authorization": f"Bearer {attacker_token}"}
    
    # 3. Attacker tries to delete victim's ride
    response = test_client.delete(f"/rides/{victim_ride.id}", headers=attacker_headers)
    
    # Expect 403 Forbidden or 404 Not Found
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

def test_invalid_jwt_format(test_client: TestClient):
    """Verify JWT format validation"""
    headers = {"Authorization": "Bearer invalid.token.format"}
    response = test_client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
