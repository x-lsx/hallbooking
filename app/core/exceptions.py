class AppError(Exception):
    """Базовое исключение приложения."""

    status_code: int = 500
    code: str = "internal_error"
    message: str = "Internal server error"

    def __init__(self, message: str | None = None, **extra):
        self.message = message or self.message
        self.extra = extra
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"
    message = "Bad request"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    message = "Not authenticated"


class PermissionDeniedError(AppError):
    status_code = 403
    code = "permission_denied"
    message = "Access denied"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "Conflict"


class UnprocessableError(AppError):   
    status_code = 422
    code = "unprocessable"
    message = "Unprocessable request"