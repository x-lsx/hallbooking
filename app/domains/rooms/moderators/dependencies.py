from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_db
from app.core.exceptions import PermissionDeniedError
from app.domains.users.models import User

from .services import RoomModeratorService


async def require_room_moderator(
    room_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
) -> User:
    service = RoomModeratorService(db)
    if not await service.can_moderate(user, room_id):
        raise PermissionDeniedError("Нет прав на этот зал")
    return user

RoomManager = Annotated[User, Depends(require_room_moderator)]