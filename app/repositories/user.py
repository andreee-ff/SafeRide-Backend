from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from typing import Sequence

from app.models import UserModel


class UserRepository:
    session: AsyncSession

    def __init__(self, *, session: AsyncSession):
        self.session = session
    
    async def create_user(self, *,  username: str, password: str) -> UserModel:
        new_user = UserModel(username=username, password=password)
        self.session.add(new_user)
        await self.session.flush()
        return new_user
     
    async def get_by_username(self, *, username: str) -> UserModel | None:
        statement = select(UserModel).where(UserModel.username == username)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_by_id(self, *, user_id: int) -> UserModel | None:
        statement = select(UserModel).where(UserModel.id == user_id)
        result =  await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_all_users(self) -> Sequence[UserModel]:
        statement = select(UserModel)
        result = await self.session.execute(statement)
        return result.scalars().all()
    
 
