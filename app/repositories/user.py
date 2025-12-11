from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from typing import Sequence

from app.models import UserModel


class UserRepository:
    session: Session

    def __init__(self, *, session: Session):
        self.session = session
    
    def create_user(self, *,  username: str, password: str) -> UserModel:
        new_user = UserModel(username=username, password=password)
        self.session.add(new_user)
        self.session.flush()

        return new_user
     
    def get_by_username(self, *, username: str) -> UserModel | None:
        statement = select(UserModel).where(UserModel.username == username)
        return self.session.execute(statement).scalar_one_or_none()
    
    def get_by_id(self, *, user_id: int) -> UserModel | None:
        statement = select(UserModel).where(UserModel.id == user_id)
        return self.session.execute(statement).scalar_one_or_none()
    
    def get_all_users(self) -> Sequence[UserModel]:
        statement = select(UserModel)
        return(self.session.execute(statement).scalars().all()) 
