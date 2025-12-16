from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status


from app.injections import (
    get_ride_repository,
)
from app.repositories import (
    RideRepository,
)

from app.schemas import (
    ParticipantResponse,
    UserResponse,
    RideResponse,
    RideCreate,
    RideUpdate,
)

from app.routers.dependencies import get_current_user

router = APIRouter()

# ------------- RIDE ROUTES ------------- #

@router.post(
    "/",
    response_model=RideResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {}},
)
async def create_ride(
    ride_to_create: RideCreate,
    ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> RideResponse:

    ride_model = await ride_repository.create_ride(
    title = ride_to_create.title,
    description = ride_to_create.description,
    start_time = ride_to_create.start_time,
    created_by_user_id = current_user.id,
    ) 
    return RideResponse.model_validate(ride_model)

create_ride.__doc__ = """
    Create a new ride.
    """
    
@router.get(
    "/",
    response_model=List[RideResponse],
    status_code=status.HTTP_200_OK
)
async def get_list_rides(
    ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
) -> List[RideResponse]:
    
    rides = await ride_repository.get_all_rides()
    return [RideResponse.model_validate(ride) for ride in rides]

get_list_rides.__doc__ = """
    Get all rides in the database.
    """

@router.get(
    "/owned",
    status_code=status.HTTP_200_OK,
    response_model=List[RideResponse],
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_owned_rides(
    ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> List[RideResponse]:
    owned_rides = await ride_repository.get_owned_rides(user_id=current_user.id)
    if not owned_rides:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return [RideResponse.model_validate(r) for r in owned_rides]

get_owned_rides.__doc__ = """
    Get all rides created by the current user.
    """

@router.get(
    "/joined",
    status_code=status.HTTP_200_OK,
    response_model=List[RideResponse],
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_joined_rides(
    ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> List[RideResponse]:
    joined_rides = await ride_repository.get_joined_rides(user_id = current_user.id)
    if not joined_rides:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return [RideResponse.model_validate(r) for r in joined_rides]

get_joined_rides.__doc__ = """
    Get all rides joined by the current user.
    """

@router.get(
    "/available",
    status_code=status.HTTP_200_OK,
    response_model=List[RideResponse],
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_available_rides(
    ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> List[RideResponse]:
    available_rides = await ride_repository.get_available_rides(user_id=current_user.id)
    if not available_rides:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return [RideResponse.model_validate(r) for r in available_rides]

get_available_rides.__doc__ = """
    Get all rides available for the current user.
    """


@router.get(
    "/code/{code}",
    response_model=RideResponse,    
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_ride_by_code(
    code: str,
    ride_repository: Annotated[
        RideRepository, Depends(get_ride_repository)
    ],
) -> RideResponse:
    ride = await ride_repository.get_by_code(ride_code=code)
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return RideResponse.model_validate(ride) 

get_ride_by_code.__doc__ = """
    Get a ride by its code.
    """

@router.get(
        "/{id}",
        response_model=RideResponse,
        status_code=status.HTTP_200_OK,
        responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_ride_by_id(
        id: int,
        ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
) -> RideResponse:
    ride = await ride_repository.get_by_id(ride_id=id)
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return RideResponse.model_validate(ride)

get_ride_by_id.__doc__ = """
    Get a ride by its id.
    """


@router.get(
    "/{ride_id}/participants",
    response_model=List[ParticipantResponse],
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_ride_participants(
    ride_id: int,
    ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
) -> List[ParticipantResponse]:
    participants = await ride_repository.get_participants(ride_id=ride_id)

    return [
        ParticipantResponse(
            id=p.id,
            user_id=p.user_id,
            username=p.participant.username,
            joined_at=p.joined_at,
            latitude=p.latitude,
            longitude=p.longitude,
            location_timestamp=p.location_timestamp,
        )
        for p in participants 
    ]

get_ride_participants.__doc__ = """
    Get all participants of a ride.
    """
    

@router.put(
    "/{id}",
    response_model=RideResponse,        
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {},       
        status.HTTP_403_FORBIDDEN: {},
    }
)
async def update_ride_by_id(
    id: int,
    ride_to_update: RideUpdate,
    ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> RideResponse:
    
    existing_ride = await ride_repository.get_by_id(ride_id=id)
    if not existing_ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    if existing_ride.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "Not allowed to update this ride. It belongs to another user",
            )
    
    ride_model = await ride_repository.update_ride(
        existing_ride,
        title = ride_to_update.title,
        description = ride_to_update.description,
        start_time = ride_to_update.start_time,
        is_active = ride_to_update.is_active,
    )
    return RideResponse.model_validate(ride_model)

update_ride_by_id.__doc__ = """
    Update a ride by its id.
    """

@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {},       
        status.HTTP_403_FORBIDDEN: {},
        },
)
async def delete_ride_by_id(
    id: int,
    ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> None:
    selected_ride = await ride_repository.get_by_id(ride_id=id)
    if not selected_ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    if selected_ride.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this ride. The ride was created by another user"
            )
    
    await ride_repository.delete_ride(ride=selected_ride)    
    return

delete_ride_by_id.__doc__ = """
    Delete a ride by its id.
    """

