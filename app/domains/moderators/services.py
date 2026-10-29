import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.rooms.exceptions import RoomNotFound
from app.domains.rooms.repository import RoomRepository
from app.domains.users.exceptions import UserNotFound
from app.domains.users.models import User
from app.domains.users.repository import UserRepository

from .exceptions import ModeratorAlreadyAssigned, ModeratorInvalid, ModeratorNotFound
from .models import RoomModerator
from .repository import RoomModeratorRepository
from .schemas import ModeratorAssign, ModeratorResponse


class RoomModeratorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = RoomModeratorRepository(db)
        self.room_repository = RoomRepository(db)
        self.user_repository = UserRepository(db)
        self.logger = logging.getLogger(__name__)

    async def can_moderate(self, user: User, room_id: int) -> bool:
        if user.is_superuser:
            return True
        return await self.repository.has_active_assignment(room_id, user.id)

    async def list_moderators(
        self, room_id: int, only_active: bool = True
    ) -> list[ModeratorResponse]:
        if not await self.room_repository.get_by_id(room_id):
            raise RoomNotFound()
        items = await self.repository.get_by_room(room_id, only_active)
        return [ModeratorResponse.model_validate(i) for i in items]

    async def get_my_room_ids(self, user: User) -> list[int]:
        assignments = await self.repository.get_by_user(user.id)
        return [a.room_id for a in assignments]

    async def assign(
        self, actor: User, room_id: int, data: ModeratorAssign
    ) -> ModeratorResponse:

        if not await self.room_repository.get_by_id(room_id):
            raise RoomNotFound()

        target = await self.user_repository.get_by_id(data.user_id)
        if target is None:
            raise UserNotFound()
        if not target.is_active:
            raise ModeratorInvalid("Пользователь деактивирован")
        if target.id == actor.id:
            raise ModeratorInvalid("Нельзя назначить самого себя")

        if not actor.is_superuser and data.valid_until is None:
            raise ModeratorInvalid(
                "Укажите срок: бессрочно назначает только администратор"
            )

        existing = await self.repository.get_open(room_id, target.id)
        if existing is not None:
            now = datetime.now(timezone.utc)
            is_active = existing.valid_until is None or existing.valid_until > now
            if is_active:
                raise ModeratorAlreadyAssigned()
            existing.revoked_at = existing.valid_until
            await self.db.flush()

        assignment = RoomModerator(
            room_id=room_id,
            user_id=target.id,
            valid_until=data.valid_until,
            granted_by=actor.id,
        )
        try:
            await self.repository.create(assignment)
            assignment_id = assignment.id
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ModeratorAlreadyAssigned() from e

        self.logger.info(
            "moderator assigned: room=%s user=%s by=%s until=%s",
            room_id,
            target.id,
            actor.id,
            data.valid_until,
        )
        created = await self.repository.get_by_id(assignment_id)
        return ModeratorResponse.model_validate(created)

    async def revoke(self, actor: User, room_id: int, assignment_id: int) -> None:
        assignment = await self.repository.get_by_id(assignment_id)

        if assignment is None or assignment.room_id != room_id:
            raise ModeratorNotFound()

        if assignment.revoked_at is None:
            assignment.revoked_at = datetime.now(timezone.utc)
            await self.db.commit()
            self.logger.info(
                "moderator revoked: room=%s user=%s by=%s",
                room_id,
                assignment.user_id,
                actor.id,
            )
