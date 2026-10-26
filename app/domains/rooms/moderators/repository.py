from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import RoomModerator


class RoomModeratorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _active_conditions():
        return (
            RoomModerator.revoked_at.is_(None),
            RoomModerator.valid_from <= func.now(),
            or_(
                RoomModerator.valid_until.is_(None),
                RoomModerator.valid_until > func.now(),
            ),
        )

    async def get_by_id(self, assignment_id: int) -> RoomModerator | None:
        stmt = (
            select(RoomModerator)
            .where(RoomModerator.id == assignment_id)
            .options(selectinload(RoomModerator.user))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_room(
        self, room_id: int, only_active: bool = False
    ) -> list[RoomModerator]:
        stmt = (
            select(RoomModerator)
            .where(RoomModerator.room_id == room_id)
            .options(selectinload(RoomModerator.user))
            .order_by(RoomModerator.valid_from.desc(), RoomModerator.id.desc())
        )
        if only_active:
            stmt = stmt.where(*self._active_conditions())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user(self, user_id: int) -> list[RoomModerator]:
        """Действующие назначения пользователя (с залами)."""
        stmt = (
            select(RoomModerator)
            .where(RoomModerator.user_id == user_id, *self._active_conditions())
            .options(selectinload(RoomModerator.room))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def has_active_assignment(self, room_id: int, user_id: int) -> bool:
        stmt = select(
            exists().where(
                RoomModerator.room_id == room_id,
                RoomModerator.user_id == user_id,
                *self._active_conditions(),
            )
        )
        return bool((await self.db.execute(stmt)).scalar())

    async def get_open(self, room_id: int, user_id: int) -> RoomModerator | None:
        """Не отозванное назначение, даже если срок уже истёк."""
        stmt = select(RoomModerator).where(
            RoomModerator.room_id == room_id,
            RoomModerator.user_id == user_id,
            RoomModerator.revoked_at.is_(None),
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def create(self, room_moderator: RoomModerator) -> RoomModerator:
        self.db.add(room_moderator)
        await self.db.flush()
        return room_moderator
