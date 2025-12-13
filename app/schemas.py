from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, ConfigDict, field_serializer,field_validator


class TimestampMixin(BaseModel):
    @field_serializer("*")# Serialize all datetime fields
    @classmethod
    def serialize_dt(cls, value, _info): 
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            iso_str = value.astimezone(timezone.utc).isoformat()
            return iso_str.replace("Z", "+00:00")
        return value
    
    model_config = ConfigDict(from_attributes=True)

#------------------------ USER

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(TimestampMixin):
    id: int
    username: str
    created_at: datetime
    updated_at: datetime


#------------------------ TOKEN

class TokenResponse(TimestampMixin):
    access_token: str
    token_type: str = "bearer"

#------------------------ RIDE
class RideBase(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime

class RideCreate(RideBase):
    pass

class RideResponse(RideBase, TimestampMixin):
    id: int
    code: str
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

class RideUpdate(RideBase):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    is_active: bool | None = None


#------------------------ PARTICIPATION
class ParticipationCreate(BaseModel):
    ride_code: str

class ParticipationUpdate(BaseModel):
    latitude: float
    longitude: float
    location_timestamp: datetime

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, value):
        if not -90 <= value <= 90:
            raise ValueError("Latitude must be between -90 and 90.")
        return value
    
    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, value):
        if not -180 <= value <= 180:
            raise ValueError("Longitude must be between -180 and 180.")
        return value
    
    @field_validator('location_timestamp')
    @classmethod
    def validate_timestamp(cls, value):
        # Make value timezone-aware if it's naive
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value
    
    
class ParticipationResponse(TimestampMixin):
    id: int
    user_id: int
    ride_id: int
    joined_at: datetime
    updated_at: datetime
    latitude: float | None = None
    longitude: float | None = None
    location_timestamp: datetime | None = None


class ParticipantResponse(TimestampMixin):
    id: int
    user_id: int
    username: str
    joined_at: datetime
    latitude: float | None = None
    longitude: float | None = None
    location_timestamp: datetime | None = None


#------------------------ SIMULATION 

class SimulationStart(BaseModel):
    ride_code: str
    count: int = 1
    username_base: str = "swarm_user"
    
class SimulationAnimate(BaseModel):
    ride_id: int

