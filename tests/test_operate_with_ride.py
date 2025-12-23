from unittest.mock import ANY

import pytest

from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RideModel, UserModel
from app.repositories import RideRepository
from tests.conftest import RideFactoryType

@pytest.mark.asyncio
async def test_create_ride_success(
    test_client: AsyncClient, 
    session: AsyncSession,
    auth_headers: dict[str, str],
 ):
    start_time = datetime(
        year=2025,
        month=11,
        day=18,
        hour=15,
        minute=30,
        tzinfo=timezone.utc,
    ).isoformat()
    payload = {
        "title": "Ride_title",
        "description": "Ride_description",
        "start_time": start_time,
    }
    response = await test_client.post("/rides/", json=payload, headers=auth_headers)

    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert isinstance(data["id"], int)
    assert isinstance(data["code"], str) and len(data["code"]) == 6
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
 
    assert datetime.fromisoformat(data["start_time"]) == datetime.fromisoformat(
        payload["start_time"].replace("Z", "+00:00")
    )
    assert isinstance(data["created_by_user_id"], int)
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)
    assert data["is_active"] is True

    result = await session.execute(
            select(RideModel).filter(RideModel.id == data["id"])
        )
    assert result.first() is not None

@pytest.mark.asyncio
async def test_get_all_rides_success(
        test_client: AsyncClient,
        ride_factory: RideFactoryType,
):
    count_ride = 3
    created_rides = []
    for _ in range(count_ride):
        ride = await ride_factory()
        created_rides.append(ride)

    response = await test_client.get("/rides/")
    assert response.status_code == status.HTTP_200_OK
    
    data_response = response.json()
    assert isinstance(data_response, list)
    assert len(data_response) == count_ride

    returned_codes = {ride['code'] for ride in data_response}
    expected_codes = {ride.code for ride in created_rides}
    assert returned_codes == expected_codes

@pytest.mark.asyncio
async def test_get_ride_by_code_success(
        test_client: AsyncClient,
        test_ride: RideModel,
):
    expected_response = {
        "id": ANY,
        "code": test_ride.code,
        "title": ANY,
        "description": ANY,
        "start_time": ANY,
        "created_by_user_id": ANY,
        "created_at": ANY,
        "updated_at": ANY,
        "is_active": ANY,
        "route_id": ANY,
        "visibility": ANY,
    }

    response = await test_client.get(f"/rides/code/{test_ride.code}")

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == expected_response

@pytest.mark.asyncio
async def test_get_ride_by_id_success(
        test_client: AsyncClient,
        test_ride: RideModel,
):
    expected_response = {
        "id": test_ride.id,
        "code": ANY,
        "title": ANY,
        "description": ANY,
        "start_time": ANY,
        "created_by_user_id": ANY,
        "created_at": ANY,
        "updated_at": ANY,
        "is_active": ANY,
        "route_id": ANY,
        "visibility": ANY,
    }

    response = await test_client.get(f"/rides/{test_ride.id}")

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == expected_response

@pytest.mark.asyncio
async def test_delete_ride_by_id_success(
        test_client: AsyncClient,
        test_ride: RideModel,
        auth_headers: dict[str, str],
        session: AsyncSession
):
    payload ={
        "title": test_ride.title,
        "description": test_ride.description,
        "start_time": test_ride.start_time.isoformat()
    }
    create_response = await test_client.post(
        "/rides/",
        json=payload,
        headers=auth_headers,
        )
    assert create_response.status_code == status.HTTP_201_CREATED, (
        f"Ride was not createtd. Expected 'HTTP_201_CREATED', but got {create_response.status_code}."
        f"Server response: {create_response.text}"
    )

    ride_id_to_delete = create_response.json()["id"]

    delete_respose = await test_client.delete(
        f"/rides/{ride_id_to_delete}",
        headers=auth_headers,
        )

    assert delete_respose.status_code == status.HTTP_204_NO_CONTENT,(
        f"Ride was not createtd. Expected 'HTTP_204_NO_CONTENT', but got {delete_respose.status_code}.\n"
        f"Server response: {delete_respose.text}"
    ) 

    session.expire_all()
    result = await session.execute(select(RideModel).where(RideModel.id == ride_id_to_delete))
    deleted_in_db = result.scalar_one_or_none()
    assert deleted_in_db is None

@pytest.mark.asyncio
async def test_edit_ride_by_id_success(
        test_client: AsyncClient,
        test_ride: RideModel,
        auth_headers: dict[str, str],
):
    create_payload = {        
        "title": test_ride.title,
        "description": test_ride.description,
        "start_time": test_ride.start_time.isoformat()
    }

    create_response = await test_client.post(
        "/rides/",
        json=create_payload,
        headers=auth_headers,
    )
    assert create_response.status_code == status.HTTP_201_CREATED, (
        f"Ride was not createtd. Expected 'HTTP_201_CREATED', but got {create_response.status_code}."
        f"Server response: {create_response.text}"
    )

    created_ride = create_response.json()

    update_payload ={
        "title": "updated_title",
        "description": "Updated_description",
        "start_time": datetime(2026,1,1,11,11,11,tzinfo=timezone.utc).isoformat(),
        "is_active": False
    }
    
    put_response = await test_client.put(
        f"/rides/{created_ride['id']}",
        json=update_payload,
        headers=auth_headers,
    )
    assert put_response.status_code == status.HTTP_200_OK, put_response.text
    
    response_data = put_response.json()
    expected_response = {
        "id": created_ride["id"],
        "code": created_ride["code"],
        "title": update_payload["title"],
        "description": update_payload["description"],
        "start_time": response_data["start_time"], 
        "created_by_user_id": created_ride["created_by_user_id"],
        "created_at": created_ride["created_at"],
        "updated_at": response_data["updated_at"],
        "is_active": update_payload["is_active"],
        "route_id": response_data["route_id"],
        "visibility": response_data["visibility"],
    }
    assert response_data == expected_response
    
@pytest.mark.asyncio
async def test_update_ride_updates_only_given_fields_without_api(session: AsyncSession):

    user = UserModel(username="creator", password="pass")
    session.add(user)
    await session.commit()

    ride_repository = RideRepository(session=session)

    old_ride = RideModel(
        code="XXXXXX",
        title="Old unit titel",
        description="Old unit description",
        start_time=datetime(2020,1,1,12,0, tzinfo=timezone.utc),
        created_by_user_id=user.id,
    )

    session.add(old_ride)
    await session.commit()

    ride_to_update = {
        "title" : "New unit title",
        "is_active" : False,
    }

    updated_ride = await ride_repository.update_ride(
        old_ride,
        title=ride_to_update["title"],
        is_active=ride_to_update["is_active"],
    )

    assert updated_ride.title == ride_to_update["title"]
    assert updated_ride.is_active == ride_to_update["is_active"]

    assert updated_ride.code == old_ride.code
    assert updated_ride.description == old_ride.description
    assert updated_ride.start_time == old_ride.start_time

    db_ride = await session.get(RideModel, old_ride.id)
    assert db_ride is not None
    assert db_ride.title == ride_to_update["title"]
    assert db_ride.is_active == ride_to_update["is_active"]

@pytest.mark.asyncio
async def test_get_all_rides_return_empty_list_when_none_exsist(
        test_client: AsyncClient,
):
    response = await test_client.get(f"/rides/")
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == []


