from datetime import time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class Building(Base, TimestampMixin):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(128))
    address: Mapped[str | None] = mapped_column(String(256))
    timezone: Mapped[str] = mapped_column(
        String(64), server_default="Asia/Yekaterinburg"
    )

    rooms: Mapped[list["Room"]] = relationship(back_populates="building")


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("building_id", "number", name="uq_rooms_building_number"),
        CheckConstraint("capacity > 0", name="ck_rooms_capacity_positive"),
        CheckConstraint("open_until > open_from", name="ck_rooms_open_hours"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="RESTRICT"), index=True
    )
    organization: Mapped[str | None] = mapped_column(String(128))
    number: Mapped[str] = mapped_column(String(32))
    name: Mapped[str | None] = mapped_column(String(128))
    capacity: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(64))
    open_from: Mapped[time] = mapped_column(Time, server_default=text("'08:00'"))
    open_until: Mapped[time] = mapped_column(Time, server_default=text("'20:00'"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    building: Mapped["Building"] = relationship(back_populates="rooms")
    moderators: Mapped[list["RoomModerator"]] = relationship(back_populates="room")
    event_formats: Mapped[list["EventFormat"]] = relationship(
        secondary="rooms_formats",
        back_populates="rooms",
    )
