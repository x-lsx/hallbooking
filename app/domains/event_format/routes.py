from fastapi import APIRouter, Depends, status
from fastapi.param_functions import Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import SuperUser
from app.db.postgres import dbDep
from app.domains.event_format.schemas import EventFormatCreate, EventFormatResponse
from app.domains.event_format.services import EventFormatService

router = APIRouter(
    prefix="/event-formats",
    tags=["event_formats"],
    )

@router.get("", response_model=list[EventFormatResponse], status_code=status.HTTP_200_OK)
async def get_event_formats(
    db: dbDep,
    ):
    event_format_service = EventFormatService(db)
    return await event_format_service.get_all_event_formats()

@router.get("/{event_format_id}", response_model=EventFormatResponse, status_code=status.HTTP_200_OK)
async def get_event_format_by_id(
    event_format_id: int,
    db: dbDep,
    ):
    event_format_service = EventFormatService(db)
    return await event_format_service.get_event_format_by_id(event_format_id)

@router.post("", response_model=EventFormatResponse, status_code=status.HTTP_201_CREATED)
async def create_event_format(
    event_format_data: EventFormatCreate,
    db: dbDep,
    current_user: SuperUser,
    ):
    event_format_service = EventFormatService(db)
    return await event_format_service.create_event_format(event_format_data)