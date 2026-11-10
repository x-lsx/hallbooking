from datetime import datetime
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Booking, BookingStatus
from .schemas import BookingFilter, BookingListFilter


class BookingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _load_options():
        return (
            selectinload(Booking.room),
            selectinload(Booking.event_format),
            selectinload(Booking.department),
            selectinload(Booking.created_by),
            selectinload(Booking.decided_by),
        )

    async def get_by_id(self, booking_id: int) -> Booking | None:
        stmt = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(*self._load_options())
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    def _list_conditions(f: BookingListFilter) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if f.statuses:
            conditions.append(Booking.status.in_(f.statuses))
        if f.room_id is not None:
            conditions.append(Booking.room_id == f.room_id)
        if f.start_at is not None:
            conditions.append(Booking.end_at > f.start_at)
        if f.end_at is not None:
            conditions.append(Booking.start_at < f.end_at)
        return conditions

    async def _list(
        self, scope: ColumnElement[bool], f: BookingListFilter
    ) -> tuple[list[Booking], int]:
        conditions = [scope, *self._list_conditions(f)]
        total = await self.db.scalar(
            select(func.count()).select_from(Booking).where(*conditions)
        )
        stmt = (
            select(Booking)
            .where(*conditions)
            .order_by(Booking.created_at.desc(), Booking.id.desc())
            .offset(f.offset)
            .limit(f.size)
        )
        return list((await self.db.scalars(stmt)).all()), total or 0

    async def list_by_user(
        self, user_id: int, f: BookingListFilter
    ) -> tuple[list[Booking], int]:
        return await self._list(Booking.created_by_id == user_id, f)

    async def list_requests_for_room(
        self, room_id: int, f: BookingListFilter
    ) -> tuple[list[Booking], int]:
        return await self._list(Booking.room_id == room_id, f)
 
    async def list_for_room(
        self,
        room_id: int,
        f: BookingFilter,
        statuses: Sequence[BookingStatus] | None = None,
    ) -> list[Booking]:
        stmt = select(Booking).where(
            Booking.room_id == room_id,
            Booking.end_at > f.start_at,
            Booking.start_at < f.end_at,
        )
        if statuses:
            stmt = stmt.where(Booking.status.in_(statuses))
        stmt = stmt.order_by(Booking.start_at, Booking.id)
        return list((await self.db.execute(stmt)).scalars().all())
 
    async def find_conflicts(
        self,
        room_id: int,
        start_at: datetime,
        end_at: datetime,
        exclude_id: int | None = None,
    ) -> list[Booking]:
        stmt = select(Booking).where(
            Booking.room_id == room_id,
            Booking.status == BookingStatus.APPROVED,
            Booking.end_at > start_at,
            Booking.start_at < end_at,
        )
        if exclude_id is not None:
            stmt = stmt.where(Booking.id != exclude_id)
        return list((await self.db.execute(stmt)).scalars().all())
 
    async def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        await self.db.flush() 
        return booking
