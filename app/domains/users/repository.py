from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import User

SEARCH_LIMIT = 20


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _with_department():
        return joinedload(User.department)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_with_department(self, user_id: int) -> User | None:

        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(self._with_department())
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_search(self, search: str, limit: int = SEARCH_LIMIT) -> list[User]:
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .options(self._with_department())
        )
        for term in search.split():
            stmt = stmt.where(
                or_(
                    User.first_name.icontains(term, autoescape=True),
                    User.last_name.icontains(term, autoescape=True),
                    User.email.icontains(term, autoescape=True),
                )
            )
        stmt = stmt.order_by(User.last_name, User.first_name, User.id).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def update(self, user_id: int, update_data: dict) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        for key, value in update_data.items():
            setattr(user, key, value)
        await self.db.flush()
        return user