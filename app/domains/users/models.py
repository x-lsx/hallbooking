from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)

    first_name: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(20), nullable=True)
    middle_name: Mapped[str | None] = mapped_column(String(20), nullable=True)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    department: Mapped["Department"] = relationship(lazy="raise")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, mail={self.email}, active={self.is_active})>"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} <{self.email}>"
