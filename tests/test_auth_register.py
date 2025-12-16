from unittest.mock import ANY

import pytest

from fastapi import status
from httpx import AsyncClient

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession 

from app.models import UserModel

@pytest.mark.asyncio 
async def test_missing_user_payload(test_client: AsyncClient):
    response = await test_client.post("/users/")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, response.text

@pytest.mark.asyncio    
async def test_register_duplicate_username(test_client: AsyncClient, session: AsyncSession):
    existing_user = UserModel(username="existing_user", password="password")
    session.add(existing_user)
    await session.commit()

    payload={"username": existing_user.username, "password": "newpassword"}

    response = await test_client.post("/users/", json=payload)

    assert response.status_code == status.HTTP_409_CONFLICT, response.text

@pytest.mark.asyncio
async def test_register_success(test_client: AsyncClient, session: AsyncSession):
    payload = {"username": "new_user", "password" : "passs123"}
    expected_response = {
        "id": ANY,
        "username": payload["username"],
        "created_at": ANY,
        "updated_at": ANY,
    }

    response = await test_client.post("/users/", json=payload)

    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert (data := response.json()) == expected_response
    result = await session.execute(
            select(UserModel).filter(UserModel.id == data["id"])
        )
    assert result.first() is not None


@pytest.mark.asyncio
async def test_get_user_by_id_success(
    test_client: AsyncClient,
    test_user: UserModel,
):
    expected_response = {
        "id": test_user.id,
        "username": test_user.username,
        "created_at": ANY,
        "updated_at": ANY,
    }

    response = await test_client.get(f"/users/{test_user.id}")

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == expected_response

                                
