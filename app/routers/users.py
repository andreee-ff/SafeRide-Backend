from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.injections import (
    get_user_repository, 
)
from app.repositories import (
    UserRepository,
)
from app.schemas import (
    UserResponse,
    UserCreate,
)


router = APIRouter()


# ------------- USER ROUTES ------------- #

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {}},
)
async def create_user(
    user_to_create: UserCreate,
    user_repository: Annotated[
        UserRepository, Depends(get_user_repository)
    ],
) -> UserResponse:
    selected_user = await user_repository.get_by_username(username=user_to_create.username)
    if selected_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    try:
        user_model = await user_repository.create_user(
            username=user_to_create.username, password=user_to_create.password
        )   
        return UserResponse.model_validate(user_model)
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT) from exception
    
@router.get(
    "/{id}",
    response_model=UserResponse,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_user(
    id: int,
    user_repository: Annotated[
        UserRepository, Depends(get_user_repository)
    ],
) -> UserResponse:
    selected_user = await user_repository.get_by_id(user_id=id)
    if not selected_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return UserResponse.model_validate(selected_user)

@router.get(
     "/",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK
)
async def get_list_users(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> List[UserResponse]:
    
    users = await user_repository.get_all_users()
    return [UserResponse.model_validate(user) for user in users]

