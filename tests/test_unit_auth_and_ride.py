from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.models import UserModel, RideModel
from app.repositories import RideRepository
import app.security as security


def test_unit_update_ride_in_riderepository(mocker):
    mock_session = mocker.MagicMock()
    ride_repository =RideRepository(session=mock_session)

    old_ride = RideModel(
        code="XXXXXX",
        title="Old unit titel",
        description="Old unit description",
        start_time=datetime(2020,1,1,12,0, tzinfo=timezone.utc),
        created_by_user_id=1,
    )

    ride_to_update = {
        "title" : "New unit title",
        "is_active" : False,
    }

    updated_ride = ride_repository.update_ride(
        old_ride,
        title=ride_to_update["title"],
        is_active=ride_to_update["is_active"],
    )

    assert updated_ride.title == ride_to_update["title"]
    assert updated_ride.is_active == ride_to_update["is_active"]

    assert updated_ride.code == old_ride.code
    assert updated_ride.description == old_ride.description
    assert updated_ride.start_time == old_ride.start_time

    mock_session.add.assert_called_once_with (updated_ride)
    mock_session.flush.assert_called_once()


def test_unit_create_and_decode_access_token(mocker):
    security.SECRET_KEY = "unit-secret-key"
    security.ALGORITHM = "HS256"
    security.ACCESS_TOKEN_EXPIRE_MINUTES = 15

    subject="test_user_subject"

    access_token = security.create_access_token(subject=subject)

    decoded_access_token = security.decode_access_token(access_token)

    assert decoded_access_token["sub"] == subject
