from unittest.mock import ANY

from fastapi import status
from fastapi.testclient import TestClient
# from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserModel

def test_login_success(
        test_client: TestClient,
        test_user: UserModel,
):
    payload = {
        "username": test_user.username,
        "password": test_user.password,
     }
    expected_response = {
        "access_token": ANY,
        "token_type": "bearer",
    }

    response = test_client.post("/auth/login/", data=payload)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert (data := response.json()) == expected_response
    assert data["access_token"] is not None

def test_login_invalid_credentials(
        test_client: TestClient,
):
    payload = {
        "username": "nonexistent_user",
        "password": "wrongpassword",
     }
    response = test_client.post("/auth/login/", data=payload)
    assert response.status_code  == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {
        "detail": "Invalid username or password"
    }

def test_login_me_with_token_success(
        test_client: TestClient,
        test_user: UserModel,
):
    login_payload = {
        "username": test_user.username,
        "password": test_user.password,
    }
    login_response = test_client.post("/auth/login/", data=login_payload)
    assert login_response.status_code == status.HTTP_200_OK, login_response.text

    token = login_response.json()["access_token"]

    response = test_client.get(
        "/auth/me/",
        headers={"Authorization": f"Bearer {token}"},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response_data["id"] == test_user.id
    assert response_data["username"] == test_user.username
    assert "created_at" in response_data
    assert "updated_at" in response_data

def test_login_me_without_token(
        test_client: TestClient,
):
    response = test_client.get("/auth/me/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {
        "detail": "Not authenticated"
    }

def test_login_me_with_invalid_token(
    test_client: TestClient,
):
    response = test_client.get(
        "/auth/me/",
        headers={"Authorization": "Bearer invalid token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {
        "detail": "Invalid token"
    }   





