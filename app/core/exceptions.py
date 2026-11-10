class AppError(Exception):
    """Базовое исключение приложения."""

    status_code: int = 500
    code: str = "internal_error"
    detail: str = "Internal server error"

    def __init__(self, message: str | None = None, **extra):
        self.detail = message if message is not None else self.detail
        self.message = self.detail
        self.extra = extra
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"
    detail = "Bad request"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    detail = "Not authenticated"


class PermissionDeniedError(AppError):
    status_code = 403
    code = "permission_denied"
    detail = "Access denied"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    detail = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    detail = "Conflict"


class UnprocessableError(AppError):   
    status_code = 422
    code = "unprocessable"
    detail = "Unprocessable request"