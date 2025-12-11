from unittest.mock import ANY

from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RideModel, UserModel, ParticipationModel
from app.schemas import ParticipationResponse
##from app.repositories import RideRepository, ParticipationRepository
from tests.conftest import RideFactoryType

def test_create_participation_success(
        test_client: TestClient,
        test_ride: RideModel,
        auth_headers: dict[str, str],
):
    payload = {
        "ride_code": test_ride.code,
    }

    response = test_client.post(
        "/participations/",
        json = payload,
        headers = auth_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text

    current_user_response = test_client.get("/auth/me", headers=auth_headers)
    assert current_user_response.status_code == status.HTTP_200_OK, current_user_response.text
    current_user_id = current_user_response.json()["id"]
    
    current_ride_response = test_client.get(f"/rides/code/{test_ride.code}")
    assert current_ride_response.status_code == status.HTTP_200_OK, current_ride_response.text
    current_ride_id =  current_ride_response.json()["id"]

    assert response.json()["user_id"] == current_user_id, response.text
    assert response.json()["ride_id"] == current_ride_id, response.text
    assert response.json()["latitude"] is None, response.text
    assert response.json()["longitude"] is None, response.text
    assert response.json()["location_timestamp"] is None, response.text

def test_get_participation_by_id_success(
        test_client: TestClient,
        test_participation: ParticipationModel,
):
    participation_response = ParticipationResponse.model_validate(test_participation)
    expected_response = participation_response.model_dump()

    response = test_client.get(f"/participations/{test_participation.id}")
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
        expected_response["updated_at"]
    )
    

def test_get_participation_by_id_returns_404_not_found(
        test_client: TestClient,
):
    wrong_id = 999

    response = test_client.get(f"/participations/{wrong_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_participation_by_id_returns_422_for_invalid_id(
        test_client: TestClient,
):
    wrong_id = "xxx"

    response = test_client.get(f"/participations/{wrong_id}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_participation_by_id_success(
        test_client: TestClient,
        test_ride: RideModel,
        auth_headers: dict[str, str],
):
    payload_to_post ={
        "ride_code": test_ride.code,
    }
    
    post_response = test_client.post(
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

    put_response = test_client.put(
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



   

    