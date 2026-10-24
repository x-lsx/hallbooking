from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_utils import decode_access_token  # должен бросать InvalidTokenError
from app.db.postgres import get_db
from app.domains.users.models import User
from app.domains.users.repository import UserRepository

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _extract_user_id(token: str) -> int:
    """Достаёт id пользователя из access-токена или бросает ValueError."""
    payload = decode_access_token(token)  # пусть бросает свои/JWT-исключения
    return int(payload.sub)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        user_id = _extract_user_id(credentials.credentials)
    except (ValueError, jwt.PyJWTError):  # см. примечание ниже
        raise _unauthorized("Invalid authentication credentials")

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise _unauthorized("User not found or inactive")
    return user


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Текущий пользователь или None, если токена нет или он невалиден."""
    if credentials is None:
        return None
    try:
        user_id = _extract_user_id(credentials.credentials)
    except (ValueError, jwt.PyJWTError):
        return None
    user = await UserRepository(db).get_by_id(user_id)
    return user if user and user.is_active else None


async def require_superuser(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
SuperUser = Annotated[User, Depends(require_superuser)]