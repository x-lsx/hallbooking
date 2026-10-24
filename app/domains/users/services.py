import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import UserNotFound
from .repository import UserRepository
from .schemas import UserResponse, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)
        self.logger = logging.getLogger(__name__)
        
    async def get_user_by_id(self, user_id: int) -> UserResponse:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(f"User with id {user_id} not found")
        return UserResponse.model_validate(user)

    async def get_user_by_email(self, email: str) -> UserResponse:
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFound(f"User with email {email} not found")
        return UserResponse.model_validate(user)
    
    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserResponse:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(f"User with id {user_id} not found")
        
        update_data = user_update.model_dump(exclude_unset=True)
        updated_user = await self.user_repository.update(user_id, update_data)
        await self.user_repository.db.commit()
        return UserResponse.model_validate(updated_user)