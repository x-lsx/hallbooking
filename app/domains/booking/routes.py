from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.param_functions import Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.postgres import dbDep
from app.domains.moderators.dependencies import RoomManager

from .schemas import (
    BookingCalendarResponse,
    BookingFilter,
    BookingOfflineCreate,
    BookingOnlineCreate,
    BookingResponse,
)
from .services import BookingService

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
)

def get_booking_service(db: dbDep) -> BookingService:
    return BookingService(db)

BookingServiceDep = Annotated[BookingService, Depends(get_booking_service)]

@router.post("", response_model=BookingResponse)
async def create_online(
    data: BookingOnlineCreate,
    actor: CurrentUser,
    service: BookingServiceDep,
):
    return await service.create_online(actor, data)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_by_id(
    booking_id: int,
    actor: CurrentUser,
    service: BookingServiceDep,
):
    return await service.get_booking(actor, booking_id)

room_router = APIRouter(prefix="/rooms/{room_id}/bookings", tags=["bookings"])

@room_router.get("",response_model=list[BookingCalendarResponse])
async def list_room_bookings(
    room_id: int,
    filters: Annotated[BookingFilter, Query()],
    actor: CurrentUser,
    service: BookingServiceDep,
):
    return await service.list_by_room(actor, room_id, filters)

@room_router.post("", response_model=BookingResponse)
async def create_offline(
    room_id: int,
    data: BookingOfflineCreate,
    actor: RoomManager,
    service: BookingServiceDep,
):
    return await service.create_offline(room_id, actor, data)