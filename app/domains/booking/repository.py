from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Booking
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

    @staticmethod
    def _apply_filter(stmt, f: BookingFilter):
        if f.start_at is not None:
            stmt = stmt.where(Booking.end_at > f.start_at)
        if f.end_at is not None:
            stmt = stmt.where(Booking.start_at < f.end_at)
        return stmt

    async def get_by_id(self, booking_id: int) -> Booking | None:
        stmt = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(*self._load_options())
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, f: BookingFilter) -> list[Booking]:
        base = self._apply_filter(select(Booking), f)
        stmt = base.order_by(
            Booking.start_at.asc()
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    
