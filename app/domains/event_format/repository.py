from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from .models import EventFormat


class EventFormatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, event_format_id: int) -> EventFormat | None:
        return await self.db.get(EventFormat, event_format_id)

    async def get_many_active(self, ids: set[int]) -> list[EventFormat]:
        stmt = select(EventFormat).where(EventFormat.id.in_(ids), EventFormat.is_active)
        return list((await self.db.scalars(stmt)).all())

    async def get_all(self) -> list[EventFormat]:
        stmt = select(EventFormat).where(EventFormat.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create(self, event_format: EventFormat) -> EventFormat:
        self.db.add(event_format)
        await self.db.flush()
        await self.db.refresh(event_format)
        return event_format