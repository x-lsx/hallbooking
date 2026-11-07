from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Department


class DepartmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: Department) -> Department:
        self.db.add(data)
        await self.db.flush()
        await self.db.refresh(data)
        return data

    async def get_by_id(self, department_id: int) -> Department | None:
        stmt = select(Department).where(Department.id == department_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Department]:
        stmt = select(Department).order_by(Department.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())