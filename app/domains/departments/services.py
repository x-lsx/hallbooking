from .models import Department
from .repository import DepartmentRepository
from .schemas import DepartmentCreate, DepartmentResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError


class DepartmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.dep_repo = DepartmentRepository(db)

    async def create(self, data: DepartmentCreate) -> DepartmentResponse:
        department = Department(**data.model_dump())
        try:
            created = await self.dep_repo.create(department)
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError("Не удалось создать подразделение: конфликт данных") from exc
        return DepartmentResponse.model_validate(created)

    async def get_by_id(self, department_id: int) -> DepartmentResponse:
        department = await self.dep_repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Подразделение не найдено")
        return DepartmentResponse.model_validate(department)

    async def get_all(self) -> list[DepartmentResponse]:
        return await self.dep_repo.get_all()
