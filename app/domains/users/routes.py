from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser
from app.db.postgres import dbDep
from app.domains.users.schemas import UserResponse
from app.domains.users.services import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"]
)


def get_user_service(db: dbDep) -> UserService:
    return UserService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    user: CurrentUser,
    service: UserServiceDep,
    ):
    return await service.get_user_by_id(user.id)


