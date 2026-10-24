from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)


class EmailAlreadyRegistered(ConflictError):
    code = "email_already_registered"
    message = "Email already registered"


class InvalidCredentials(UnauthorizedError):
    code = "invalid_credentials"
    message = "Invalid email or password"


class InvalidRefreshToken(UnauthorizedError):
    code = "invalid_refresh_token"
    message = "Invalid or expired refresh token"


class RefreshTokenRevoked(UnauthorizedError):
    code = "refresh_token_revoked"
    message = "Refresh token has been revoked"


class InvalidVerificationToken(BadRequestError):
    code = "invalid_verification_token"
    message = "Invalid or expired verification token"


class InvalidResetToken(BadRequestError):
    code = "invalid_reset_token"
    message = "Invalid or expired password reset token"


class WrongOldPassword(BadRequestError):
    code = "wrong_old_password"
    message = "Invalid old password"


class SamePassword(BadRequestError):
    code = "same_password"
    message = "New password must be different from the old one"