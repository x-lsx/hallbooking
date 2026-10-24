from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pydantic import ValidationError

from app.core.config import settings
from app.domains.auth.token_schemas import AccessTokenPayload, RefreshTokenPayload


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),          
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.ACCESS_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: int) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid4())

    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": jti,
        "type": "refresh",
    }

    token = jwt.encode(
        payload,
        settings.REFRESH_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, jti


def decode_access_token(token: str) -> AccessTokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.ACCESS_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = AccessTokenPayload.model_validate(payload)

        if token_data.type != "access":
            raise jwt.InvalidTokenError("Invalid token type")

        return token_data

    except (jwt.PyJWTError, ValidationError) as exc:
        raise jwt.InvalidTokenError("Invalid or expired access token") from exc


def decode_refresh_token(token: str) -> RefreshTokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.REFRESH_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = RefreshTokenPayload.model_validate(payload)

        if token_data.type != "refresh":
            raise jwt.InvalidTokenError("Invalid token type")

        return token_data

    except (jwt.PyJWTError, ValidationError) as exc:
        raise jwt.InvalidTokenError("Invalid or expired refresh token") from exc