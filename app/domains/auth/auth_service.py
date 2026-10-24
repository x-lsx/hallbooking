import logging

import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.security import hashed_password, verify_password
from app.db.redis import Redis
from app.domains.auth.schemas import ChangePassword, UserCreate
from app.domains.users.exceptions import UserNotFound
from app.domains.users.repository import UserRepository
from app.tasks.send_confirmation_email import send_confirmation_email
from app.tasks.send_reset_password_email import send_password_reset_email
from app.tasks.test import login_debug_task

from .exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidRefreshToken,
    InvalidResetToken,
    InvalidVerificationToken,
    RefreshTokenRevoked,
    SamePassword,
    WrongOldPassword,
)
from .token_schemas import TokenResponse
from .token_service import TokenService


def build_token_response(
    access_token: str,
    refresh_token: str,
) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.user_repository = UserRepository(db)
        self.token_service = TokenService(redis)
        self.logger = logging.getLogger(__name__)
        
    async def register_user(self, user_create: UserCreate) -> TokenResponse:
        existing_user = await self.user_repository.get_by_email(user_create.email)
        if existing_user:
            raise EmailAlreadyRegistered()

        user_data = user_create.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_password(user_create.password)

        new_user = await self.user_repository.create(user_data)
        await self.user_repository.db.commit()

        access_token = create_access_token(new_user.id)
        refresh_token, jti = create_refresh_token(new_user.id)

        await self.token_service.save_refresh_token(new_user.id, jti)

        token = await self.token_service.generate_verification_token(new_user.id)
        send_confirmation_email.delay(to_email=new_user.email,
                                      verify_url=f"{
                                          settings.API_URL}/auth/verify?token={token}",
                                      )

        return build_token_response(access_token, refresh_token)

    async def authenticate_user(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentials()
        access_token = create_access_token(user.id)
        refresh_token, jti = create_refresh_token(user.id)

        await self.token_service.save_refresh_token(user.id, jti)

        login_debug_task(user.id, user.email)

        return build_token_response(access_token, refresh_token)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            token_data = decode_refresh_token(refresh_token)
        except jwt.InvalidTokenError:
            raise InvalidRefreshToken()
        exists = await self.token_service.validate_refresh_token(token_data.jti)
        if not exists:
            raise RefreshTokenRevoked()
    
        user = await self.user_repository.get_by_id(int(token_data.sub))
        if not user:
            raise InvalidRefreshToken()
        await self.token_service.revoke_refresh_token(token_data.jti)

        new_access_token = create_access_token(user.id)
        new_refresh_token, new_jti = create_refresh_token(user.id)

        await self.token_service.save_refresh_token(user.id, new_jti)

        return build_token_response(new_access_token, new_refresh_token)

    async def logout(self, refresh_token: str):
        try:
            token_data = decode_refresh_token(refresh_token)
        except jwt.InvalidTokenError:
            raise InvalidRefreshToken()
        await self.token_service.revoke_refresh_token(token_data.jti)

    async def verify_user(self, verification_token: str):
        user_id = await self.token_service.get_user_id_by_verification_token(verification_token)
        if not user_id:
            raise InvalidVerificationToken()
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFound()
        user.is_verified = True
        await self.user_repository.db.commit()
        await self.token_service.revoke_verification_token(verification_token)

    async def change_password(self, user_id: int, data: ChangePassword):
        user = await self.user_repository.get_by_id(user_id=user_id)
        if not user:
            raise UserNotFound()
        if not verify_password(data.old_password, user.hashed_password):
            raise WrongOldPassword()
        if verify_password(data.new_password, user.hashed_password):
            raise SamePassword()
        hashed_new_password = hashed_password(data.new_password)
        await self.user_repository.update(
            user_id,
            {"hashed_password": hashed_new_password}
        )
        await self.user_repository.db.commit()

        await self.token_service.revoke_all_refresh_tokens(user_id)

    async def request_password_reset(self, email: str):
        user = await self.user_repository.get_by_email(email)

        if user:
            self.logger.info("User find")
            token = await self.token_service.generate_password_reset_token(user.id)

            send_password_reset_email.delay(
                to_email=user.email,
                reset_url=f"{
                    settings.FRONTEND_URL}/auth/reset-password?token={token}",
            )
            return
        self.logger.info("user not found")
        return

    async def confirm_reset_password(self, token: str, new_password: str):
        user_id = await self.token_service.get_user_id_by_password_reset_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )
        
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        
        hashed_new_password = hashed_password(new_password)
        if verify_password(new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from the old one"
            )
        
        await self.user_repository.update(
            user_id,
            {"hashed_password": hashed_new_password}
        )

        await self.user_repository.db.commit()
        await self.token_service.revoke_password_reset_token(token)
        await self.token_service.revoke_all_refresh_tokens(user_id)
