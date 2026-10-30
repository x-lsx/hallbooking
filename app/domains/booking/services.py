from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.domains.moderators.services import RoomModeratorService
from app.domains.rooms.exceptions import RoomNotFound
from app.domains.rooms.models import Room
from app.domains.rooms.repository import RoomRepository
from app.domains.users.models import User

from .exceptions import (
    BookingConflict,
    BookingInvalid,
    BookingNotFound,
    BookingStateError,
)
from .models import Booking, BookingStatus, SourceType
from .repository import BookingRepository
from .schemas import (
    BookingCalendarResponse,
    BookingFilter,
    BookingOfflineCreate,
    BookingOnlineCreate,
    BookingResponse,
)

TIME_STEP_MINUTES = 15
MIN_DURATION = timedelta(minutes=45)


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.room_repo = RoomRepository(db)
        self.moder_serv = RoomModeratorService(db)

    async def create_online(self, actor: User, data: BookingOnlineCreate) -> BookingResponse:
        room = await self._get_room(data.room_id)
        self._validate_slot(
            room,
            data.start_at,
            data.end_at,
            data.attendees_count,
            data.event_format_id,
        )
        department_id = data.department_id or actor.department_id
        if department_id is None:
            raise BookingInvalid("Укажите подразделение")
 
        booking = Booking(
            title=data.title,
            room_id=room.id,
            event_id=data.event_format_id,
            department_id=department_id,
            created_by_id=actor.id,
            attendees_count=data.attendees_count,
            is_public=data.is_public,
            start_at=data.start_at,
            end_at=data.end_at,
            source=SourceType.ONLINE,
            status=BookingStatus.PENDING,
        )
        async with self._guard():
            await self.repository.create(booking)
            booking_id = booking.id
            await self.db.commit()
 
        self.logger.info("booking created (online): id=%s room=%s by=%s", booking_id, room.id, actor.id)
        new_booking = await self.booking_repo.get_by_id(booking_id)
        return BookingResponse.model_validate(new_booking)
        
    async def create_offline(self, room_id: int, actor: User, data: BookingOfflineCreate) -> BookingResponse:
        room = await self._get_room(room_id)
        self._validate_slot(
            room,
            data.start_at,
            data.end_at,
            data.attendees_count,
            data.event_format_id,
        )
        conflicts = await self.repository.find_conflicts(room.id, data.start_at, data.end_at)
        if conflicts:
            raise BookingConflict(self._conflict_message(conflicts, room))
        
        booking = Booking(
            title=data.title,
            requster_first_name=data.requester_first_name,
            requster_last_name=data.requester_last_name,
            requster_middle_name=data.requester_middle_name,
            requster_phone=data.requester_phone,
            created_by_id=actor.id,
            room_id=room.id,
            event_id=data.event_format_id,
            department_id=data.department_id,
            deceided_by_id=actor.id,
            source=SourceType.OFFLINE,
            status=BookingStatus.APPROVED,
            attendees_count=data.attendees_count,
            is_public=data.is_public,
            start_at=data.start_at,
            end_at=data.end_at,
            reject_reason=None,
        )
        async with self._guard():
            await self.repository.create(booking)
            booking_id = booking.id
            await self.db.commit()
 
        self.logger.info("booking created (offline): id=%s room=%s by=%s", booking_id, room.id, actor.id)
        new_booking = await self.booking_repo.get_by_id(booking_id)
        return BookingResponse.model_validate(new_booking)

    async def list_by_room(
        self, actor: User, room_id: int, f: BookingFilter
    ) -> list[BookingCalendarResponse]:

        await self._get_room(room_id)

        bookings = await self.booking_repo.list_for_room(room_id, f)
        is_moderator = await self.moder_serv.can_moderate(actor, room_id)
        statuses = (
            [BookingStatus.PENDING, BookingStatus.APPROVED]
            if is_moderator
            else [BookingStatus.APPROVED]
        )
        bookings = await self.repository.list_for_room(room_id, f, statuses)
        return [
            BookingCalendarResponse(
                id=b.id,
                title=b.title if (is_moderator or b.is_public) else "Занято",
                start_at=b.start_at,
                end_at=b.end_at,
                status=b.status,
            )
            for b in bookings
        ]

    async def get_booking(self, actor: User, booking_id: int) -> BookingResponse:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise NotFoundError(message="Booking not found.")
        if (booking.created_by_id != actor.id) and (
            not await self.moder_serv.can_moderate(actor, booking.room_id)
        ):
            raise NotFoundError(message="Booking not found.")

        return BookingResponse.model_validate(booking)

    async def _get_room(self, room_id: int) -> Room:
        room = await self.room_repository.get_by_id(room_id)
        if room is None:
            raise RoomNotFound()
        return room

    async def _require_moderator(self, actor: User, room_id: int) -> None:
        if not await self.moderators.can_moderate(actor, room_id):
            raise PermissionDeniedError("Нет прав на этот зал")

    async def _get_for_moderation(
        self, actor: User, booking_id: int
    ) -> tuple[Booking, Room]:
        booking = await self.repository.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFound()
        await self._require_moderator(actor, booking.room_id)
        room = await self._get_room(booking.room_id)
        return booking, room

    @staticmethod
    def _validate_slot(
        room: Room,
        start_at: datetime,
        end_at: datetime,
        attendees_count: int,
        event_format_id: int,
    ) -> None:

        if not room.is_active:
            raise BookingInvalid("Зал недоступен для записи")
        if start_at <= datetime.now(UTC):
            raise BookingInvalid("Нельзя создать запись в прошлом")

        tz = ZoneInfo(room.building.timezone)
        local_start = start_at.astimezone(tz)
        local_end = end_at.astimezone(tz)

        if local_start.date() != local_end.date():
            raise BookingInvalid("Запись должна начинаться и заканчиваться в один день")
        for moment in (local_start, local_end):
            if moment.minute % TIME_STEP_MINUTES or moment.second or moment.microsecond:
                raise BookingInvalid(
                    f"Время должно быть кратно {TIME_STEP_MINUTES} минутам"
                )
        if end_at - start_at < MIN_DURATION:
            raise BookingInvalid("Запись слишком короткая")
        if local_start.time() < room.open_from or local_end.time() > room.open_until:
            raise BookingInvalid(
                f"Зал работает с {room.open_from:%H:%M} до {room.open_until:%H:%M}"
            )
        if attendees_count > room.capacity:
            raise BookingInvalid(f"Вместимость зала: {room.capacity}")

        if room.formats and event_format_id not in {f.id for f in room.formats}:
            raise BookingInvalid("Этот формат не поддерживается залом")


    @staticmethod
    def _conflict_message(conflicts: list[Booking], room: Room) -> str:
        tz = ZoneInfo(room.building.timezone)
        parts = []
        for c in conflicts[:3]:
            s, e = c.start_at.astimezone(tz), c.end_at.astimezone(tz)
            parts.append(f"«{c.title}» {s:%d.%m %H:%M}–{e:%H:%M}")
        return "Зал занят в это время: " + "; ".join(parts)