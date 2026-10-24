from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)