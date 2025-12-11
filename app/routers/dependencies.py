from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException , status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.injections import (
    get_user_repository, 
)
from app.repositories import (
    UserRepository,
)
from app.schemas import (
    UserResponse,
)
from app.security import create_access_token, decode_access_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],  
) -> UserResponse:
    try:
        payload = decode_access_token(token)

        sub = payload.get("sub")
        if sub is None:
            raise JWTError("Subject not found in token")
        
        user_id = int(sub)
    
    except (ValueError, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
        
    user = user_repository.get_by_id(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return UserResponse.model_validate(user)
