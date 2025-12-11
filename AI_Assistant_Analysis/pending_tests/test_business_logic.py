from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timezone

def test_ride_codes_are_unique(test_client: TestClient, auth_headers: dict[str, str]):
    """Verify that consecutive ride creation generates different codes"""
    # Create first ride
    payload1 = {
        "title": "Ride 1",
        "description": "Desc 1",
        "start_time": datetime(2025, 12, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat()
    }
    response1 = test_client.post("/rides/", json=payload1, headers=auth_headers)
    assert response1.status_code == status.HTTP_201_CREATED
    code1 = response1.json()["code"]
    
    # Create second ride
    payload2 = {
        "title": "Ride 2",
        "description": "Desc 2",
        "start_time": datetime(2025, 12, 1, 11, 0, 0, tzinfo=timezone.utc).isoformat()
    }
    response2 = test_client.post("/rides/", json=payload2, headers=auth_headers)
    assert response2.status_code == status.HTTP_201_CREATED
    code2 = response2.json()["code"]
    
    # Assert codes are different
    assert code1 != code2

def test_participation_requires_valid_ride(test_client: TestClient, auth_headers: dict[str, str]):
    """Verify cannot create participation for nonexistent ride"""
    payload = {
        "ride_code": "NONEXISTENT_CODE_999"
    }
    
    response = test_client.post("/participations/", json=payload, headers=auth_headers)
    
    # Should return 404 Not Found (or 400 Bad Request depending on implementation)
    # Based on roadmap we expect 404
    assert response.status_code == status.HTTP_404_NOT_FOUND
