from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.room_formats.models import RoomFormat


class RoomFormatsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: int) -> RoomFormat | None:
        stmt = select(RoomFormat).where(RoomFormat.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> list[RoomFormat]:
        stmt = select(RoomFormat)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def list_by_room_id(self, room_id: int) -> list[RoomFormat]:
        stmt = select(RoomFormat).where(RoomFormat.room_id == room_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, room_format: RoomFormat) -> RoomFormat:
        self.db.add(room_format)
        await self.db.flush()
        await self.db.refresh(room_format)
        return room_format
    
    async def delete(self, room_format: RoomFormat) -> bool:
        await self.db.delete(room_format)
        await self.db.flush()