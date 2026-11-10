from fastapi import APIRouter, status

from app.core.dependencies import SuperUser
from app.db.postgres import dbDep

from .schemas import DepartmentCreate, DepartmentResponse
from .services import DepartmentService

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED,)
async def create_department(
    data: DepartmentCreate,
    actor: SuperUser,
    db: dbDep,
):
    service = DepartmentService(db)
    return await service.create(data)


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
)
async def get_department(
    department_id: int,
    db: dbDep,
):
    service = DepartmentService(db)
    return await service.get_by_id(department_id)


@router.get("", response_model=list[DepartmentResponse])
async def get_departments(db: dbDep):
    service = DepartmentService(db)
    return await service.get_all()
