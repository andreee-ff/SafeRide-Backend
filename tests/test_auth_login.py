from unittest.mock import ANY

import pytest

from fastapi import status
from httpx import AsyncClient

from app.models import UserModel



@pytest.mark.asyncio
async def test_login_success(
        test_client: AsyncClient,
        test_user: UserModel,
):
    payload = {
        "username": test_user.username,
        "password": "testpassword",
     }
    expected_response = {
        "access_token": ANY,
        "token_type": "bearer",
    }

    response = await test_client.post("/auth/login", data=payload)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert (data := response.json()) == expected_response
    assert data["access_token"] is not None

@pytest.mark.asyncio
async def test_login_invalid_credentials(
        test_client: AsyncClient,
):
    payload = {
        "username": "nonexistent_user",
        "password": "wrongpassword",
     }
    response = await test_client.post("/auth/login", data=payload)
    assert response.status_code  == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {
        "detail": "Invalid username or password"
    }

@pytest.mark.asyncio
async  def test_login_me_with_token_success(
        test_client: AsyncClient,
        test_user: UserModel,
):
    login_payload = {
        "username": test_user.username,
        "password": "testpassword",
    }
    login_response = await test_client.post("/auth/login", data=login_payload)
    assert login_response.status_code == status.HTTP_200_OK, login_response.text

    token = login_response.json()["access_token"]

    response = await test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response_data["id"] == test_user.id
    assert response_data["username"] == test_user.username
    assert "created_at" in response_data
    assert "updated_at" in response_data

@pytest.mark.asyncio
async def test_login_me_without_token(
        test_client: AsyncClient,
):
    response = await test_client.get("/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {
        "detail": "Not authenticated"
    }

@pytest.mark.asyncio
async def test_login_me_with_invalid_token(
    test_client: AsyncClient,
):
    response = await test_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {
        "detail": "Invalid token"
    }   
