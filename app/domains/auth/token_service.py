import hashlib
import secrets

from app.core.config import settings
from app.db.redis import Redis


class TokenService:
    def __init__(self, redis: Redis):
        self.redis: Redis = redis

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    # refresh token methods

    async def save_refresh_token(self, user_id: int, jti: str) -> None:
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(f"refresh_token:{jti}", user_id, ex=ttl)
            pipe.sadd(f"user_tokens:{user_id}", jti)
            pipe.expire(f"user_tokens:{user_id}", ttl)
            await pipe.execute()

    async def revoke_refresh_token(self, jti: str) -> None:
        user_id = await self.redis.get(f"refresh_token:{jti}")
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.delete(f"refresh_token:{jti}")
            if user_id is not None:
                pipe.srem(f"user_tokens:{user_id}", jti)
            await pipe.execute()

    async def validate_refresh_token(self, jti: str) -> bool:
        return bool(await self.redis.exists(f"refresh_token:{jti}"))

    async def revoke_all_refresh_tokens(self, user_id: int) -> None:
        jtis = await self.redis.smembers(f"user_tokens:{user_id}")
        if not jtis:
            return
        async with self.redis.pipeline(transaction=True) as pipe:
            for jti in jtis:
                pipe.delete(f"refresh_token:{jti}")
            pipe.delete(f"user_tokens:{user_id}")
            await pipe.execute()

    # verification token methods

    async def generate_verification_token(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        await self.redis.set(
            f"verification_token:{self._hash(token)}",
            user_id,
            ex=settings.VERIFICATION_TOKEN_EXPIRE_HOURS * 60 * 60,
        )
        return token

    async def revoke_verification_token(self, token: str) -> None:
        await self.redis.delete(f"verification_token:{self._hash(token)}")

    async def get_user_id_by_verification_token(self, token: str) -> int | None:
        user_id = await self.redis.get(f"verification_token:{self._hash(token)}")
        if user_id is None:
            return None
        return int(user_id)

    # reset password token methods

    async def generate_password_reset_token(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        await self.redis.set(
            f"password_reset_token:{self._hash(token)}",
            user_id,
            ex=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS * 60 * 60,
        )
        return token

    async def revoke_password_reset_token(self, token: str) -> None:
        await self.redis.delete(f"password_reset_token:{self._hash(token)}")

    async def get_user_id_by_password_reset_token(self, token: str) -> int | None:
        user_id = await self.redis.get(f"password_reset_token:{self._hash(token)}")
        if user_id is None:
            return None
        return int(user_id)
