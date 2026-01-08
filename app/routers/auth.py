from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException , status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError

from app.injections import (
    get_user_repository, 
)
from app.repositories import (
    UserRepository,
)
from app.schemas import (
    UserResponse,
    TokenResponse,
)
from app.security import create_access_token, verify_password
from app.routers.dependencies import get_current_user


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ------------- AUTH ROUTES ------------- #
@router.post(
    "/login",
    response_model=TokenResponse,
    responses={status.HTTP_401_UNAUTHORIZED: {}},    
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> TokenResponse:
    user = await user_repository.get_by_username(username=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={status.HTTP_401_UNAUTHORIZED: {}},
)
async def get_me(current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> UserResponse:
    return current_user
