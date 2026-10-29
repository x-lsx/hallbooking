from datetime import datetime
from enum import Enum as PythonEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    column,
    func,
    literal_column,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.mixins import TimestampMixin
from app.db.postgres import Base


def _enum_values(enum_cls) -> list[str]:
    return [member.value for member in enum_cls]


class SourceType(str, PythonEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class BookingStatus(str, PythonEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "canselled"


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="ck_bookings_valid_time"),
        CheckConstraint("attendees_count > 0", name="ck_bookings_attendees_positive"),
        ExcludeConstraint(
            ("room_id", "="),
            (
                func.tstzrange(
                    column("start_at"), column("end_at"), literal_column("'[)'")
                ),
                "&&",
            ),
            name="ex_bookings_no_overlap",
            using="gist",
            where=text("status = 'approved'"),
        ),
        Index("ix_bookings_room_start", "room_id", "start_at"),
        Index("ix_bookings_status", "status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)

    requster_first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    requster_last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    requster_middle_name: Mapped[str] = mapped_column(String(128), nullable=False)
    requster_phone: Mapped[str] = mapped_column(String(20), nullable=False)

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="RESTRICT"))
    event_id: Mapped[int] = mapped_column(
        ForeignKey("event_formats.id", ondelete="RESTRICT")
    )
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"),
    )
    decided_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    source: Mapped[str] = mapped_column(
        Enum(SourceType, name="source_type", values_callable=_enum_values),
        default=SourceType.OFFLINE,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(BookingStatus, name="booking_status", values_callable=_enum_values),
        default=BookingStatus.PENDING,
        nullable=False,
    )
    attendees_count: Mapped[int] = mapped_column(Integer(), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    room: Mapped["Room"] = relationship(lazy="raise")
    event_format: Mapped["EventFormat"] = relationship(lazy="raise")
    department: Mapped["Department"] = relationship(lazy="raise")
    created_by: Mapped["User"] = relationship(
        foreign_keys=[created_by_id], lazy="raise"
    )
    decided_by: Mapped["User | None"] = relationship(
        foreign_keys=[decided_by_id], lazy="raise"
    )
