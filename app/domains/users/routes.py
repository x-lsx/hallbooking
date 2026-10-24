from fastapi import APIRouter, Depends, status
from fastapi.param_functions import Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user
from app.db.postgres import get_db
from app.db.redis import get_redis
from app.domains.users.schemas import UserResponse
from app.domains.users.services import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"]
)


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    user: CurrentUser,
    ):
    return user


