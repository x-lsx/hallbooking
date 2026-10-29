from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.param_functions import Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.moderators.dependencies import RoomManager
from app.core.dependencies import require_superuser, SuperUser
from app.core.paginations import PaginatedResponse
from app.db.postgres import get_db
from app.domains.moderators.routes import router as moderators_router
from app.domains.rooms.schemas import (
    RoomCreate,
    RoomUpdate,
    RoomFilter,
    RoomResponse,
)
from app.domains.rooms.services import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=PaginatedResponse[RoomResponse])
async def list(f: Annotated[RoomFilter, Query()], db: AsyncSession = Depends(get_db)):
    service = RoomService(db)
    return await service.list(f)


@router.get("/{room_id}", response_model=RoomResponse)
async def get(room_id: int, db: AsyncSession = Depends(get_db)):
    service = RoomService(db)
    return await service.get_room_by_id(room_id)

@router.post("", response_model=RoomResponse)
async def create(
    data: RoomCreate,
    user: SuperUser,
    db: AsyncSession = Depends(get_db),
    ):
    service = RoomService(db)
    return await service.create_room(data)

@router.patch("/{room_id}", response_model=RoomResponse)
async def update(
    room_id: int,
    data: RoomUpdate,
    user: RoomManager,
    db: AsyncSession = Depends(get_db),
    ):
    service = RoomService(db)
    return await service.update(room_id, data)

router.include_router(moderators_router)
