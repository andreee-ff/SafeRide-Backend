from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.repositories import RouteRepository
from app.schemas import RouteResponse, RouteCreate, RouteUpdate, UserResponse
from app.injections import get_route_repository
from app.routers.dependencies import get_current_user

router = APIRouter()

# ------------- GET ------------- #

@router.get(
    "/",
    response_model=List[RouteResponse],
    status_code=status.HTTP_200_OK,
)
async def get_list_routes(
    route_repository: Annotated[RouteRepository, Depends(get_route_repository)],
) -> List[RouteResponse]:
    """Get all routes in the database."""
    routes = await route_repository.get_all_routes()
    return [RouteResponse.model_validate(route) for route in routes]

get_list_routes.__doc__ = "Get all routes in the database."


@router.get(
    "/owned",
    status_code=status.HTTP_200_OK,
    response_model=List[RouteResponse],
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_owned_routes(
    route_repository: Annotated[RouteRepository, Depends(get_route_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> List[RouteResponse]:
    """Get all routes created by the current user."""
    owned_routes = await route_repository.get_owned_routes(user_id=current_user.id)
    if not owned_routes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No routes found")
    return [RouteResponse.model_validate(route) for route in owned_routes]

get_owned_routes.__doc__ = "Get all routes created by the current user."


@router.get(
    "/{id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_route_by_id(
    id: int,
    route_repository: Annotated[RouteRepository, Depends(get_route_repository)],
) -> RouteResponse:
    """Get a route by its id."""
    route = await route_repository.get_by_id(route_id=id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    return RouteResponse.model_validate(route)

get_route_by_id.__doc__ = "Get a route by its id."


# ------------- POST ------------- #

@router.post(
    "/",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {}},
)
async def create_route(
    route_to_create: RouteCreate,
    route_repository: Annotated[RouteRepository, Depends(get_route_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> RouteResponse:
    """Create a new route."""
    route_model = await route_repository.create_route(
        title=route_to_create.title,
        description=route_to_create.description,
        gpx_data=route_to_create.gpx_data,
        created_by_user_id=current_user.id,
    )
    return RouteResponse.model_validate(route_model)

create_route.__doc__ = "Create a new route."


# ------------- PUT ------------- #

@router.put(
    "/{id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {},
        status.HTTP_403_FORBIDDEN: {},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {},
        },
)
async def update_route_by_id(
    id: int,
    route_to_update: RouteUpdate,
    route_repository: Annotated[RouteRepository, Depends(get_route_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> RouteResponse:
    """Update a route by its id."""
    existing_route = await route_repository.get_by_id(route_id=id)
    if not existing_route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    if existing_route.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to update this route",
            )

    route_model = await route_repository.update_route(
        existing_route,
        title=route_to_update.title,
        description=route_to_update.description,
        gpx_data=route_to_update.gpx_data,
    )
    return RouteResponse.model_validate(route_model)


# ------------- DELETE ------------- #

@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {},
        status.HTTP_403_FORBIDDEN: {},
        },
)
async def delete_route_by_id(
    id: int,
    route_repository: Annotated[RouteRepository, Depends(get_route_repository)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> None:
    """Delete a route by its id."""
    selected_route = await route_repository.get_by_id(route_id=id)
    if not selected_route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
            )

    if selected_route.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this route",
            )
    await route_repository.delete_route(route = selected_route)
    return
