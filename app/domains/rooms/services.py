import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnprocessableError
from app.core.paginations import PaginatedResponse
from app.domains.event_format.models import EventFormat
from app.domains.event_format.repository import EventFormatRepository
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
    RoomCreate,
    RoomFilter,
    RoomResponse,
    RoomUpdate,
)


class RoomService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.room_repository = RoomRepository(db)
        self.formats_repository = EventFormatRepository(db)
        self.building_repository = BuildingRepository(db)
        self.logger = logging.getLogger(__name__)

    async def _get_room_or_404(self, room_id: int) -> Room:
        room = await self.room_repository.get_by_id(room_id)
        if room is None:
            raise RoomNotFound()
        return room

    async def _resolve_formats(self, ids: list[int]) -> list[EventFormat]:
        unique_ids = set(ids)
        if not unique_ids:
            return []
        found = await self.formats_repository.get_many_active(unique_ids)
        missing = unique_ids - {f.id for f in found}
        if missing:
            raise UnprocessableError(
                f"Форматы не найдены или неактивны: {sorted(missing)}"
            )
        return found


    async def get_room_by_id(self, room_id: int) -> RoomResponse:
        return RoomResponse.model_validate(await self._get_room_or_404(room_id))

    async def list(self, f: RoomFilter) -> PaginatedResponse[RoomResponse]:
        rooms, total = await self.room_repository.list(f)
        return PaginatedResponse[RoomResponse](
            items=rooms, total=total, page=f.page, size=f.size
        )

    async def create_room(self, data: RoomCreate) -> RoomResponse:
        if await self.building_repository.get_by_id(data.building_id) is None:
            raise BuildingNotFound()
        if await self.room_repository.get_by_number(data.building_id, data.number):
            raise RoomConflict()

        event_formats = await self._resolve_formats(data.event_format_ids)
        room = Room(
            **data.model_dump(exclude={"event_format_ids"}),
            event_formats=event_formats,
        )
        try:
            await self.room_repository.create(room)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise RoomConflict()
        return RoomResponse.model_validate(room)


    async def update(self, room_id: int, data: RoomUpdate) -> RoomResponse:
        room = await self._get_room_or_404(room_id)
        changes = data.model_dump(exclude_unset=True, exclude={"event_format_ids"})

        building_id = changes.get("building_id", room.building_id)
        number = changes.get("number", room.number)
        open_from = changes.get("open_from", room.open_from)
        open_until = changes.get("open_until", room.open_until)

        if open_until <= open_from:
            raise UnprocessableError(
                "Время закрытия должно быть позже времени открытия"
            )

        if "building_id" in changes and (
            await self.building_repository.get_by_id(building_id) is None
        ):
            raise BuildingNotFound()

        if "building_id" in changes or "number" in changes:
            existing = await self.room_repository.get_by_number(building_id, number)
            if existing and existing.id != room.id:
                raise RoomConflict()

        for key, value in changes.items():
            setattr(room, key, value)

        if data.event_format_ids is not None:
            room.event_formats = await self._resolve_formats(data.event_format_ids)

        try:
            await self.db.flush()
            await self.db.refresh(room, ["building", "event_formats"])
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise RoomConflict("Нарушено ограничение данных аудитории")
        return RoomResponse.model_validate(room)

    async def deactivate(self, room_id: int) -> None:
        room = await self._get_room_or_404(room_id)
        room.is_active = False
        await self.db.commit()


class BuildingService:
    def __init__(self, db: AsyncSession):
        self.db = db
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

    async def create_building(
        self, data: BuildingCreate
    ) -> BuildingResponse:
        building = Building(**data.model_dump())
        try:
            await self.building_repository.create(building)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            self.logger.warning("Конфликт при создании здания: %s", data.number)
            raise BuildingConflict()
        return BuildingResponse.model_validate(building)
