from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class EventFormat(Base, TimestampMixin):
    __tablename__ = "event_formats"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


    rooms: Mapped[list["Room"]] = relationship(
        secondary="rooms_formats",
        back_populates="event_formats",
    )
    def __repr__(self) -> str:
        return f"<EventFormat(id={self.id}, name={self.name}, active={self.is_active})>"

    def __str__(self) -> str:
        return f"{self.name}"