import pytest
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_ride_codes_are_unique(test_client: AsyncClient, auth_headers: dict[str, str]):
    """Verify that consecutive ride creation generates different codes"""
    # Create first ride
    payload1 = {
        "title": "Ride 1",
        "description": "Desc 1",
        "start_time": datetime(2025, 12, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat()
    }
    response1 = await test_client.post("/rides/", json=payload1, headers=auth_headers)
    assert response1.status_code == status.HTTP_201_CREATED
    code1 = response1.json()["code"]
    
    # Create second ride
    payload2 = {
        "title": "Ride 2",
        "description": "Desc 2",
        "start_time": datetime(2025, 12, 1, 11, 0, 0, tzinfo=timezone.utc).isoformat()
    }
    response2 = await test_client.post("/rides/", json=payload2, headers=auth_headers)
    assert response2.status_code == status.HTTP_201_CREATED
    code2 = response2.json()["code"]
    
    # Assert codes are different
    assert code1 != code2

@pytest.mark.asyncio
async def test_participation_requires_valid_ride(test_client: AsyncClient, auth_headers: dict[str, str]):
    """Verify cannot create participation for nonexistent ride"""
    payload = {
        "ride_code": "NONEXISTENT_CODE_999"
    }
    
    # Note: Ensure the endpoint expects "ride_code" in payload. 
    # Based on previous tests, the endpoint is /participations/ and it takes RideCode payload?
    # Let's verify payload structure if this fails, but previously seen tests used ride_code in payload.
    
    response = await test_client.post("/participations/", json=payload, headers=auth_headers)
    
    # Should return 404 Not Found
    assert response.status_code == status.HTTP_404_NOT_FOUND
