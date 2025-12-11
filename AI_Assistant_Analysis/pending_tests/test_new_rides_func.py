from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.models import RideModel


def test_get_owned_rides_success(
    test_client: TestClient,
    auth_headers: dict[str, str],
):
    # 1. Create a ride
    start_time = datetime(
        2025, 11, 18, 15, 30, tzinfo=timezone.utc
    ).isoformat()
    payload = {
        "title": "Owned Ride",
        "description": "My owned ride",
        "start_time": start_time,
    }
    create_response = test_client.post(
        "/rides/", json=payload, headers=auth_headers
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    ride_id = create_response.json()["id"]

    # 2. Fetch owned rides
    response = test_client.get("/rides/owned", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # Verify our created ride is in the list
    found = False
    for ride in data:
        if ride["id"] == ride_id:
            assert ride["title"] == payload["title"]
            found = True
            break
    assert found


def test_get_joined_rides_success(
    test_client: TestClient,
    test_ride: RideModel,  # Made by some other user (factory)
    auth_headers: dict[str, str],  # Our current test user
):
    # 1. Join the ride
    join_payload = {"ride_code": test_ride.code}
    join_response = test_client.post(
        "/participations/", json=join_payload, headers=auth_headers
    )
    assert join_response.status_code == status.HTTP_201_CREATED

    # 2. Fetch joined rides
    response = test_client.get("/rides/joined", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # Verify the joined ride is in the list
    found = False
    for ride in data:
        if ride["id"] == test_ride.id:
            assert ride["code"] == test_ride.code
            found = True
            break
    assert found
