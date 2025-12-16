from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import  joinedload
from sqlalchemy import select

from typing import Sequence
import secrets, string

from app.models import ParticipationModel, RideModel


class RideRepository:
    session: AsyncSession

    def __init__ (self, *, session: AsyncSession):
        self.session = session

    def _generate_string_code(self, length: int = 6) -> str:
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    async def _generate_unique_code(self) -> str:
        while True:
            code = self._generate_string_code()
            statement = select(RideModel).where(RideModel.code == code)
            result = await self.session.execute(statement)
            existintg_ride = result.scalar_one_or_none()

            if existintg_ride is None:
                return code
            
    async def create_ride(
            self,
            *,
            title: str,
            description: str | None,
            start_time: datetime,
            created_by_user_id: int,
        ) -> RideModel:
        unique_code = await self._generate_unique_code()
        new_ride = RideModel(
            code=unique_code,
            title=title,
            description=description,
            start_time=start_time,
            created_by_user_id=created_by_user_id,
        ) 

        self.session.add(new_ride)
        await self.session.flush()
        await self.session.refresh(new_ride)

        # Create participation for the creator
        new_participation = ParticipationModel(
            ride_id=new_ride.id,
            user_id=created_by_user_id,
        )

        self.session.add(new_participation)
        await self.session.flush()    

        return new_ride

    async def get_all_rides(self) -> Sequence[RideModel]:
        statement = select(RideModel)
        result = await self.session.execute(statement)
        return result.scalars().all()
    
    async def get_participants(self, *, ride_id: int) -> Sequence[ParticipationModel]:
        statement = (
            select(ParticipationModel)
            .options(joinedload(ParticipationModel.participant))
            .where(ParticipationModel.ride_id == ride_id)
        )
        result = await self.session.execute(statement)
        return result.unique().scalars().all()
 

    async def get_by_code(self, *, ride_code: str) -> RideModel | None:
        statement = select(RideModel).where(RideModel.code == ride_code)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_by_id(self, *, ride_id: int) -> RideModel | None:
        statement = select(RideModel).where(RideModel.id == ride_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_owned_rides(self, *, user_id: int) -> Sequence[RideModel]:
        statement = select(RideModel).where(
            RideModel.created_by_user_id == user_id
            ).order_by(RideModel.start_time.asc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_joined_rides(self, *, user_id: int) -> Sequence[RideModel]:
        statement = select(RideModel).where(
            RideModel.has_participants.any(
                ParticipationModel.user_id == user_id
                )).order_by(RideModel.start_time.asc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_available_rides(self, *, user_id: int) -> Sequence[RideModel]:
        statement = select(RideModel).where(
            ~RideModel.has_participants.any(
                ParticipationModel.user_id == user_id
            )
        ).order_by(RideModel.start_time.asc())
        result = await self.session.execute(statement)
        return result.scalars().all()


# ------------- UPDATE & DELETE ------------- #


    async def update_ride(
            self,
            ride: RideModel,         
            *,           
            title: str | None = None,
            description: str | None = None,
            start_time: datetime | None = None,
            is_active: bool | None = None,
        ) -> RideModel:
        ride_to_update ={
            "title": title,
            "description": description,
            "start_time": start_time,
            "is_active": is_active,
        }

        for key, value in ride_to_update.items():
            if value is not None:
                setattr(ride, key, value)

        self.session.add(ride)
        await self.session.flush()
        await self.session.refresh(ride)
        return ride

    async def delete_ride(self, *, ride: RideModel) -> None:
        await self.session.delete(ride)
        await self.session.flush()
