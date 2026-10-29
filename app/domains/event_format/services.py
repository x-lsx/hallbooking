from sqlalchemy.ext.asyncio import AsyncSession

from .models import EventFormat
from .repository import EventFormatRepository
from .schemas import EventFormatCreate, EventFormatResponse


class EventFormatService:
    def __init__(self, db: AsyncSession):
        self.event_format_repository = EventFormatRepository(db)

    async def get_event_format_by_id(self, event_format_id: int) -> EventFormatResponse:
        event_format = await self.event_format_repository.get_by_id(event_format_id)
        if not event_format:
            raise ValueError("Event format not found")
        return EventFormatResponse.model_validate(event_format)

    async def get_all_event_formats(self) -> list[EventFormatResponse]:
        event_formats = await self.event_format_repository.get_all()
        return [EventFormatResponse.model_validate(ef) for ef in event_formats]

    
    async def create_event_format(
        self, event_format_create: EventFormatCreate
    ) -> EventFormatResponse:
        event_format = EventFormat(**event_format_create.model_dump())
        created_event_format = await self.event_format_repository.create(event_format)
        await self.event_format_repository.db.commit()
        return EventFormatResponse.model_validate(created_event_format)
