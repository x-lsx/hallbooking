from datetime import time, datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Time,
    UniqueConstraint,
    func,
    DateTime,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class RoomModerator(Base, TimestampMixin):
    __tablename__ = "room_moderators"
    __table_args__ = (
        Index(
            "uq_room_moderators_open",
            "room_id",
            "user_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_room_moderators_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    granted_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    room: Mapped["Room"] = relationship(back_populates="moderators")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
