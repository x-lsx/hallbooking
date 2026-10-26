import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.rooms.exceptions import (
    BuildingConflict,
    BuildingNotFound,
    RoomConflict,
    RoomNotFound,
)
from app.domains.rooms.models import Building, Room

from .repository import BuildingRepository, RoomRepository
from .schemas import (
    BuildingCreate,
    BuildingResponse,
    BuildingUpdate,
    RoomCreate,
    RoomCreatedResponse,
    RoomResponse,
    RoomUpdate,
)


class RoomService:
    def __init__(self, db: AsyncSession):
        self.room_repository = RoomRepository(db)
        self.building_repository = BuildingRepository(db)
        self.logger = logging.getLogger(__name__)

    async def get_room_by_id(self, room_id: int) -> RoomResponse:
        room = await self.room_repository.get_by_id(room_id)
        if not room:
            raise RoomNotFound()
        return RoomResponse.model_validate(room)

    async def get_room_by_number(self, number: str) -> RoomResponse:
        room = await self.room_repository.get_by_number(number)
        if not room:
            raise RoomNotFound()
        return RoomResponse.model_validate(room)

    async def get_all_rooms(self) -> list[RoomResponse]:
        rooms = await self.room_repository.get_all()
        return [RoomResponse.model_validate(room) for room in rooms]

    async def get_rooms_by_building_number(self, building_number: str) -> list[RoomResponse]:
        rooms = await self.room_repository.get_by_building_number(building_number)
        return [RoomResponse.model_validate(room) for room in rooms]
    
    async def create_room(self, room_create: RoomCreate) -> RoomCreatedResponse:
        if not await self.building_repository.get_by_id(room_create.building_id):
            raise BuildingNotFound()
        room = Room(**room_create.model_dump())
        try:
            await self.room_repository.create(room)
            await self.room_repository.db.commit()
        except IntegrityError as e:
            await self.room_repository.db.rollback()
            raise RoomConflict() from e
        return RoomCreatedResponse.model_validate(room)
        
    async def update_room(self, room_id: int, room_update: RoomUpdate) -> RoomResponse:
        room = await self.room_repository.get_by_id(room_id)
        if not room:
            raise RoomNotFound()
        
        update_data = room_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(room, key, value)
        
        try:
            await self.room_repository.db.commit()
            await self.room_repository.db.refresh(room)
        except IntegrityError as e:
            await self.room_repository.db.rollback()
            raise RoomConflict() from e
        
        return RoomResponse.model_validate(room)
    
class BuildingService:
    def __init__(self, db: AsyncSession):
        self.building_repository = BuildingRepository(db)
        self.logger = logging.getLogger(__name__)

    async def get_building_by_id(self, building_id: int) -> BuildingResponse:
        building = await self.building_repository.get_by_id(building_id)
        if not building:
            raise BuildingNotFound()
        return BuildingResponse.model_validate(building)

    async def get_all_buildings(self) -> list[BuildingResponse]:
        buildings = await self.building_repository.get_all()
        return [BuildingResponse.model_validate(building) for building in buildings]
    
    async def create_building(self, building_create: BuildingCreate) -> BuildingResponse:
        building = Building(**building_create.model_dump())
        try:
            await self.building_repository.create(building)
            await self.building_repository.db.commit()
        except IntegrityError as e:
            await self.building_repository.db.rollback()
            print(e)
            raise BuildingConflict()
        return BuildingResponse.model_validate(building)