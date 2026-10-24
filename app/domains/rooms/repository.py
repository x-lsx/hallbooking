from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Room


class RoomRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_by_id(self, room_id: int) -> Room | None:
        return await self.db.get(Room, room_id)
    
    async def get_by_number()