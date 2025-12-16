from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from typing import Sequence

from app.models import ParticipationModel

class ParticipationRepository:
    session: AsyncSession

    def __init__(self, *, session: AsyncSession):
        self.session = session

    async def create_participation(
            self,
            *,
            user_id: int,
            ride_id: int,
    ) -> ParticipationModel:
        new_participation = ParticipationModel(
            user_id = user_id,
            ride_id = ride_id,
        )

        self.session.add(new_participation)

        try:
            await self.session.flush()
            await self.session.refresh(new_participation)
        except IntegrityError as exc:
            msg = str(exc)
            if "uix_user_ride" in msg or "UNIQUE constraint failed: participations.user_id, participations.ride_id" in msg:
                raise ValueError("User has already joined this ride.") from exc
            raise

        return new_participation
    
    async def get_by_id(self, *, participation_id: int) -> ParticipationModel | None:
        result = await self.session.get(ParticipationModel, participation_id)
        return result
    
    async def get_all_participations(self) -> Sequence[ParticipationModel]:
        statement = select(ParticipationModel)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_ride_id(self, *, ride_id: int) -> Sequence[ParticipationModel]:
        statement = (
            select(ParticipationModel)
            .where(ParticipationModel.ride_id == ride_id)
            .options(joinedload(ParticipationModel.participant))
        )
        result = await self.session.execute(statement)
        return result.scalars().all()



    async def get_by_user_and_ride(self, *, user_id: int, ride_id: int) -> ParticipationModel | None:
        statement = (
            select(ParticipationModel).where(
                ParticipationModel.user_id == user_id,
                ParticipationModel.ride_id == ride_id,
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def update_participation(
        self,
        participation: ParticipationModel,
        *,
        latitude: float,
        longitude: float, 
        location_timestamp: datetime
    ) -> ParticipationModel:
        
        participation_to_update = {
            "latitude": latitude,
            "longitude": longitude,
            "location_timestamp": location_timestamp,
        }

        for key, value in participation_to_update.items():
            if value is not None:
                setattr(participation, key, value)

        self.session.add(participation)
        await self.session.flush()
        await self.session.refresh(participation)

        return participation

    async def delete_participation(
        self,
        *, 
        participation: ParticipationModel,
        ) -> None:
        await self.session.delete(participation)
        await self.session.flush()
