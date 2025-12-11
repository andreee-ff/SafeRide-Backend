from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.repositories import UserRepository, RideRepository, ParticipationRepository

def get_session(request: Request) -> Generator[Session]:
    with (session := Session(bind=request.app.state.database_engine)).begin():
        yield session

def get_user_repository(
        session: Annotated[Session, Depends(get_session)]
) -> UserRepository:
    return UserRepository(session=session)

def get_ride_repository(
        session: Annotated[Session, Depends(get_session)]
) -> RideRepository:
    return RideRepository(session=session)

def get_participation_repository(
        session: Annotated[Session, Depends(get_session)]
) -> ParticipationRepository:
    return ParticipationRepository(session=session)

