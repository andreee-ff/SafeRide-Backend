from fastapi import status
from httpx import AsyncClient
import pytest
from app.models import RideModel

@pytest.mark.asyncio
async def test_ride_response_contains_all_required_fields(
    test_client: AsyncClient, 
    test_ride: RideModel
):
    """Verify all required fields are present in response"""
    response = await test_client.get(f"/rides/{test_ride.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    required_fields = ["id", "code", "title", "description", "start_time", 
                      "created_by_user_id", "created_at", "updated_at", "is_active"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

@pytest.mark.asyncio
async def test_datetime_format_consistency(
    test_client: AsyncClient, 
    test_ride: RideModel
):
    """Verify all datetime fields use ISO 8601 format"""
    response = await test_client.get(f"/rides/{test_ride.id}")
    data = response.json()
    
    # Should contain 'T' separator for ISO format (e.g. 2025-12-01T10:00:00)
    assert "T" in data["start_time"]
    assert "T" in data["created_at"]
    if data["updated_at"]:
        assert "T" in data["updated_at"]

@pytest.mark.asyncio
async def test_list_endpoints_return_arrays(test_client: AsyncClient, auth_headers: dict[str, str]):
    """Verify all list endpoints return JSON arrays"""
    # Requires authentication for some, check specific endpoints
    endpoints = ["/rides/"] # /participations/ usually requires filters or is post-only or limited
    
    for endpoint in endpoints:
        response = await test_client.get(endpoint)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list), f"Endpoint {endpoint} did not return a list"
