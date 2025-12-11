from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime
from app.models import RideModel

def test_invalid_datetime_format(test_client: TestClient, auth_headers: dict[str, str]):
    """Verify datetime format validation"""
    payload = {
        "title": "Test Invalid Date",
        "description": "Desc",
        "start_time": "invalid-date-format"  # Invalid format
    }
    response = test_client.post("/rides/", json=payload, headers=auth_headers)
    
    # 422 Unprocessable Entity is expected for FastAPIs Pydantic validation errors
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_extreme_coordinates(
    test_client: TestClient, 
    auth_headers: dict[str, str], 
    test_ride: RideModel
):
    """Verify extreme lat/long values are accepted or validated"""
    # Note: If the backend validates lat (-90 to 90) and long (-180 to 180), this might fail with 422.
    # If it uses raw float without strict validation, it might pass (201).
    # The roadmap assumption was 201 (accepted).
    
    payload = {
        "ride_code": test_ride.code,
    }
    response = test_client.post("/participations/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    participation_id = response.json()["id"]

    # Update with extreme coordinates
    update_payload = {
        "latitude": 90.0,
        "longitude": 180.0,
        "location_timestamp": datetime.now().isoformat()
    }
    response = test_client.put(f"/participations/{participation_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["latitude"] == 90.0
    assert data["longitude"] == 180.0

def test_special_characters_in_title(test_client: TestClient, auth_headers: dict[str, str]):
    """Verify special characters are accepted and potentially sanitized"""
    # XSS payload or just special chars
    special_title = "Test & <script>alert('xss')</script> 😀"
    
    payload = {
        "title": special_title,
        "description": "Desc",
        "start_time": "2025-12-01T10:00:00Z"
    }
    response = test_client.post("/rides/", json=payload, headers=auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    # Ensure it was saved (sanitization logic depends on backend implementation, usually stored as is in DB)
    assert data["title"] == special_title

def test_very_long_title(test_client: TestClient, auth_headers: dict[str, str]):
    """Verify title length constraints"""
    # Most DB strings are 255 chars, or TEXT.
    long_title = "A" * 1000 
    payload = {
        "title": long_title,
        "description": "Desc",
        "start_time": "2025-12-01T10:00:00Z"
    }
    response = test_client.post("/rides/", json=payload, headers=auth_headers)
    
    # Should either succeed (if TEXT) or fail with 422 (if constrained by Pydantic) or 500 (if DB error)
    # Ideally should be handled gracefully. Pydantic default string has no max length unless specified.
    # We assert 201 or 422, ensuring no crash (500).
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]
