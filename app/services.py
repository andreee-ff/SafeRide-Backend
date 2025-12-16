from datetime import datetime
from app.database import AsyncSessionLocal
from app.repositories import ParticipationRepository, RideRepository


class LocationService:
    @staticmethod
    async def process_location_update(
        user_id: int,
        ride_code: str,
        latitude: float,
        longitude: float,
        location_timestamp: str | datetime,
    ): 
        async with AsyncSessionLocal() as session:
            ride_repository = RideRepository(session=session)
            participation_repository = ParticipationRepository(session=session)

            ride = await ride_repository.get_by_code(ride_code=ride_code)
            if not ride:
                raise ValueError(f"Service Warning: Ride {ride_code} not found")

            participation = await participation_repository.get_by_user_and_ride(
                user_id=user_id,
                ride_id=ride.id,
            )

            if participation:
        
                if isinstance(location_timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(location_timestamp)
                    except ValueError:
                        raise ValueError("Service Warning: Invalid location timestamp format")
                else:
                    timestamp = location_timestamp

                await participation_repository.update_participation(
                    participation=participation,
                    latitude=float(latitude),
                    longitude=float(longitude),
                    location_timestamp=timestamp,
                )
            else:
                raise ValueError(f"Service Warning: User {user_id} not found in ride {ride_code}")      
    
    @staticmethod
    async def validate_ride(ride_code: str) -> bool:
        async with AsyncSessionLocal() as session:
            ride_repository = RideRepository(session=session)
            ride = await ride_repository.get_by_code(ride_code=ride_code)
            return ride is not None
