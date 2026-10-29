from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.event_format.models import EventFormat

from .models import Building, Room
from .schemas import RoomFilter


class RoomRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _load_options():
        return (
            selectinload(Room.building),
            selectinload(Room.event_formats),
        )

    @staticmethod
    def _apply_filter(stmt, f: RoomFilter):
        if f.building_id is not None:
            stmt = stmt.where(Room.building_id == f.building_id)
        if f.capacity_min is not None:
            stmt = stmt.where(Room.capacity >= f.min_capacity)
        if f.type is not None:
            stmt = stmt.where(Room.type == f.type)
        if f.is_active is not None:
            stmt = stmt.where(Room.is_active == f.is_active)
        if f.formats_ids:
            for format_id in set(f.formats_ids):
                stmt = stmt.where(
                    Room.event_formats.any(EventFormat.id == format_id)
                )
        return stmt

    async def get_by_id(self, room_id: int) -> Room | None:
        stmt = (
            select(Room)
            .where(Room.id == room_id)
            .options(*self._load_options())
        )
        return await self.db.scalar(stmt)

    async def get_by_number(self, building_id: int, number: str) -> Room | None:
        stmt = (
            select(Room)
            .where(Room.building_id == building_id, Room.number == number)
            .options(*self._load_options())
        )
        return await self.db.scalar(stmt)

    async def list(self, f: RoomFilter) -> tuple[list[Room], int]:
        base = self._apply_filter(select(Room), f)
        total = await self.db.scalar(
            select(func.count()).select_from(base.subquery())
        )
        stmt = (
            base.options(*self._load_options())
            .order_by(Room.building_id, Room.number, Room.id)
            .offset(f.offset)
            .limit(f.size)
        )
        return list((await self.db.scalars(stmt)).all()), total or 0

    async def create(self, room: Room) -> Room:
        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room, ["building", "event_formats"])
        return room
    
      
class BuildingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_by_id(self, building_id: int):
        return await self.db.get(Building, building_id)
    
    async def get_all(self):
        stmt = select(Building)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create(self, building: Building):
        self.db.add(building)
        await self.db.flush()
        await self.db.refresh(building)
        return building