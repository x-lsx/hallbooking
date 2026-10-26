from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Building, Room
from .schemas import RoomFilter


class RoomRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    @staticmethod 
    async def _filter_rooms(stmt, filter: RoomFilter):
        if filter.building_id is not None:
            stmt = stmt.where(Room.building_id == filter.building_id)
        if filter.min_capacity is not None:
            stmt = stmt.where(Room.capacity >= filter.min_capacity)
        if filter.type is not None:
            stmt = stmt.where(Room.type == filter.type)
        # if filter.formats_ids:
        #     stmt = stmt.where(Room.format_id.in_(filter.formats_ids))
        if filter.is_active is not None:
            stmt = stmt.where(Room.is_active == filter.is_active)

    async def get_by_id(self, room_id: int) -> Room | None:
        stmt = select(Room).where(Room.id == room_id).options(selectinload(Room.building))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_number(self, number: str) -> Room | None:
        stmt = select(Room).where(Room.number == number).options(selectinload(Room.building))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self) -> list[Room]:
        stmt = select(Room).options(selectinload(Room.building)).order_by(Room.number)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create(self, room: Room) -> Room:
        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room)
        return room
    
    async def get_by_building_number(self, building_number: str) -> list[Room]:
        stmt = (select(Room)
            .join(Room.building)
            .where(Building.number == building_number)
            .options(selectinload(Room.building)))
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    
    
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