from sqlalchemy import (
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class RoomFormat(Base, TimestampMixin):
    __tablename__ = "rooms_formats"
    __table_args__ = (
        UniqueConstraint("room_id", "event_format_id", name="uq_room_format"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), index=True
    )
    event_format_id: Mapped[int] = mapped_column(
        ForeignKey("event_formats.id", ondelete="CASCADE"), index=True
    )