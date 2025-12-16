from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal

from app.repositories import UserRepository, RideRepository, ParticipationRepository

# def get_session(request: Request) -> Generator[Session]:
#     with (session := Session(bind=request.app.state.database_engine)).begin():
#         yield session

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

def get_user_repository(
        session: Annotated[AsyncSession, Depends(get_session)]
) -> UserRepository:
    return UserRepository(session=session)

def get_ride_repository(
        session: Annotated[AsyncSession, Depends(get_session)]
) -> RideRepository:
    return RideRepository(session=session)

def get_participation_repository(
        session: Annotated[AsyncSession, Depends(get_session)]
) -> ParticipationRepository:
    return ParticipationRepository(session=session)

