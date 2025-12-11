from unittest.mock import ANY
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserModel

def test_missing_user_payload(test_client: TestClient):
    response = test_client.post("/users/")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, response.text

def test_register_duplicate_username(test_client: TestClient, session: Session):
    existing_user = UserModel(username="existing_user", password="password")
    session.add(existing_user)
    session.flush()

    payload={"username": existing_user.username, "password": "newpassword"}

    response = test_client.post("/users/", json=payload)

    assert response.status_code == status.HTTP_409_CONFLICT, response.text

def test_register_success(test_client: TestClient, session: Session):
    payload = {"username": "new_user", "password" : "passs123"}
    expected_response = {
        "id": ANY,
        "username": payload["username"],
        "created_at": ANY,
        "updated_at": ANY,
    }

    response = test_client.post("/users/", json=payload)

    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert (data := response.json()) == expected_response
    assert (
        session.execute(
            select(UserModel).filter(UserModel.id == data["id"])
        ).first()
        is not None
    )


def test_get_user_by_id_success(
    test_client: TestClient,
    test_user: UserModel,
):
    expected_response = {
        "id": test_user.id,
        "username": test_user.username,
        "created_at": ANY,
        "updated_at": ANY,
    }

    response = test_client.get(f"/users/{test_user.id}")

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == expected_response

                                
