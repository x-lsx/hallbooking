from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()
    
    async def get_by_search(self, search: str) -> list[User]:
        result = await self.db.execute(
            select(User).where(func.concat(User.first_name, " ", User.last_name).ilike(f"%{search}%"))
            )
        
        return result.scalars().all()
    
    async def create(self, user_data: dict) -> User:
        user = User(**user_data)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def update(self, user_id: int, update_data: dict) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for key, value in update_data.items():
            setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user