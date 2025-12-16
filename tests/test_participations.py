from unittest.mock import ANY
import pytest
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timezone

from app.models import RideModel, ParticipationModel
from app.schemas import ParticipationResponse

@pytest.mark.asyncio
async def test_create_participation_success(
        test_client: AsyncClient,
        test_ride: RideModel,
        auth_headers: dict[str, str],
):
    payload = {
        "ride_code": test_ride.code,
    }

    response = await test_client.post(
        "/participations/",
        json = payload,
        headers = auth_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text

    current_user_response = await test_client.get("/auth/me", headers=auth_headers)
    assert current_user_response.status_code == status.HTTP_200_OK, current_user_response.text
    current_user_id = current_user_response.json()["id"]
    
    current_ride_response = await test_client.get(f"/rides/code/{test_ride.code}")
    assert current_ride_response.status_code == status.HTTP_200_OK, current_ride_response.text
    current_ride_id =  current_ride_response.json()["id"]

    assert response.json()["user_id"] == current_user_id, response.text
    assert response.json()["ride_id"] == current_ride_id, response.text
    assert response.json()["latitude"] is None, response.text
    assert response.json()["longitude"] is None, response.text
    assert response.json()["location_timestamp"] is None, response.text

@pytest.mark.asyncio
async def test_get_participation_by_id_success(
        test_client: AsyncClient,
        test_participation: ParticipationModel,
):
    participation_response = ParticipationResponse.model_validate(test_participation)
    expected_response = participation_response.model_dump()

    if expected_response["location_timestamp"] and isinstance(expected_response["location_timestamp"], datetime):
        expected_response["location_timestamp"] = expected_response["location_timestamp"].isoformat().replace("+00:00", "Z")
    
    # Handle joined_at serialization if it exists in the response model dump
    if "joined_at" in expected_response and expected_response["joined_at"] and isinstance(expected_response["joined_at"], datetime):
         expected_response["joined_at"] = expected_response["joined_at"].isoformat().replace("+00:00", "Z")


    # Note: Depending on pydantic version and configuration, model_dump might result in datetime objects or strings.
    # The tests asserted raw json response (strings) against expecting strings.
    # Let's align with the manual fix strategy: Use response json vs expected values.

    response = await test_client.get(f"/participations/{test_participation.id}")
    assert response.status_code == status.HTTP_200_OK, response.text

    data = response.json()

    key_to_check = ["id", "user_id", "ride_id"]
    for key in key_to_check:
        assert isinstance(data[key], int)
        assert data[key] == expected_response[key]

    key_to_check_float = ["latitude", "longitude"]
    for key in key_to_check_float:
        assert isinstance(data[key], float)
        assert data[key] == float(expected_response[key])

    assert datetime.fromisoformat(data["updated_at"]) == datetime.fromisoformat(
        str(expected_response["updated_at"])
    )
    

@pytest.mark.asyncio
async def test_get_participation_by_id_returns_404_not_found(
        test_client: AsyncClient,
):
    wrong_id = 999
    response = await test_client.get(f"/participations/{wrong_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_participation_by_id_returns_422_for_invalid_id(
        test_client: AsyncClient,
):
    wrong_id = "xxx"
    response = await test_client.get(f"/participations/{wrong_id}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_update_participation_by_id_success(
        test_client: AsyncClient,
        test_ride: RideModel,
        auth_headers: dict[str, str],
):
    payload_to_post ={
        "ride_code": test_ride.code,
    }
    
    post_response = await test_client.post(
        "/participations/",
        json = payload_to_post,
        headers = auth_headers,
    )

    assert post_response.status_code == status.HTTP_201_CREATED, post_response.text

    old_data = post_response.json()

    payload_to_update ={
        "latitude": 40.7128,
        "longitude": -74.0060,
        "location_timestamp": datetime(2026,1,1,11,11,11,tzinfo=timezone.utc).isoformat(),
    }

    put_response = await test_client.put(
        f"/participations/{old_data['id']}",
        json = payload_to_update,
        headers = auth_headers,
    )
    assert put_response.status_code == status.HTTP_200_OK, put_response.text

    new_data = put_response.json()

    key_to_check_old= ["id", "user_id", "ride_id"]
    for key in key_to_check_old:
        assert new_data[key] == old_data[key]

    assert new_data["latitude"] == payload_to_update["latitude"]
    assert new_data["longitude"] == payload_to_update["longitude"]

    assert datetime.fromisoformat(new_data["location_timestamp"]) == datetime.fromisoformat(
        payload_to_update["location_timestamp"]
    )