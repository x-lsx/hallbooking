from datetime import datetime

from sqlalchemy import Sequence, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Booking, BookingStatus
from .schemas import BookingFilter


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