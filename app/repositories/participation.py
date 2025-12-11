from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from typing import Sequence



from app.models import ParticipationModel

class ParticipationRepository:
    session: Session

    def __init__(self, *, session: Session):
        self.session = session

    def create_participation(
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
            self.session.flush()
        except IntegrityError as exc:
            if "uix_user_ride" in str(exc):
                raise ValueError("User has already joined this ride.") from exc
            raise

        return new_participation
    
    def get_by_id(self, *, participation_id: int) -> ParticipationModel | None:
        return self.session.get(ParticipationModel, participation_id)
    
    def get_all_participations(self) -> Sequence[ParticipationModel]:
        statement = select(ParticipationModel)
        return (self.session.execute(statement).scalars().all())

    def get_by_ride_id(self, *, ride_id: int) -> Sequence[ParticipationModel]:
        statement = (
            select(ParticipationModel)
            .where(ParticipationModel.ride_id == ride_id)
            .options(joinedload(ParticipationModel.participant))
        )
        return self.session.execute(statement).scalars().all()

    def update_participation(
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
        self.session.flush()

        return participation

    def delete_participation(
        self,
        *, 
        participation: ParticipationModel,
        ) -> None:
        self.session.delete(participation)
        self.session.flush()
