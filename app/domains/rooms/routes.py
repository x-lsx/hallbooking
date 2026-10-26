from fastapi import APIRouter, Depends, status
from fastapi.param_functions import Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_superuser
from app.db.postgres import get_db
from app.domains.rooms.moderators.routes import router as moderators_router
from app.domains.rooms.schemas import RoomCreate, RoomCreatedResponse, RoomResponse
from app.domains.rooms.services import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post(
    "",
    response_model=RoomCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_superuser)],
)
async def create_room(
    room_data: RoomCreate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    room_service = RoomService(db)
    return await room_service.create_room(room_data)


@router.get("", response_model=list[RoomResponse], status_code=status.HTTP_200_OK)
async def get_rooms(
    db: AsyncSession = Depends(get_db),
):
    room_service = RoomService(db)
    return await room_service.get_all_rooms()


@router.get("/{room_id}", response_model=RoomResponse, status_code=status.HTTP_200_OK)
async def get_room_by_id(
    room_id: int,
    db: AsyncSession = Depends(get_db),
):
    room_service = RoomService(db)
    return await room_service.get_room_by_id(room_id)


router.include_router(moderators_router)
