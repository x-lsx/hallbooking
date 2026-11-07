from .models import Department
from .repository import DepartmentRepository
from .schemas import DepartmentCreate, DepartmentResponse

from sqlalchemy.ext.asyncio import AsyncSession


class DepartmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.dep_repo = DepartmentRepository(db)

    async def create(self, data: DepartmentCreate) -> DepartmentResponse:
        department = Department(**data.model_dump())
        created = await self.dep_repo.create(department)
        await self.db.commit()
        return DepartmentResponse.model_validate(created)

    async def get_by_id(self, department_id: int) -> DepartmentResponse | None:
        return await self.dep_repo.get_by_id(department_id)

    async def get_all(self) -> list[DepartmentResponse]:
        return await self.dep_repo.get_all()