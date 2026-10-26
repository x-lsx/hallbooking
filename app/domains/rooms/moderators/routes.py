from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db

from .dependencies import RoomManager, require_room_moderator
from .schemas import ModeratorAssign, ModeratorResponse
from .services import RoomModeratorService

router = APIRouter(prefix="/{room_id}/moderators", tags=["moderators"])


@router.get(
    "",
    response_model=list[ModeratorResponse],
    dependencies=[Depends(require_room_moderator)],
    responses={
        403: {"description": "Нет прав на зал"},
        404: {"description": "Зал не найден"},
    },
)
async def list_moderators(
    room_id: int,
    only_active: Annotated[bool, Query()] = True,
    db: AsyncSession = Depends(get_db),
):
    service = RoomModeratorService(db)
    return await service.list_moderators(room_id, only_active)


@router.post(
    "",
    response_model=ModeratorResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Нарушено правило назначения"},
        403: {"description": "Нет прав на зал"},
        404: {"description": "Зал или пользователь не найден"},
        409: {"description": "Пользователь уже назначен"},
    },
)
async def assign_moderator(
    room_id: int,
    data: ModeratorAssign,
    actor: RoomManager,
    db: AsyncSession = Depends(get_db)
):
    service = RoomModeratorService(db)
    return await service.assign(actor, room_id, data)


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"description": "Нет прав на зал"},
        404: {"description": "Назначение не найдено"},
    },
)
async def revoke_moderator(
    room_id: int,
    assignment_id: int,
    actor: RoomManager,
    db: AsyncSession = Depends(get_db)
):
    service = RoomModeratorService(db)
    await service.revoke(actor, room_id, assignment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
