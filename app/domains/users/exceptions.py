from app.core.exceptions import ConflictError, NotFoundError


class UserNotFound(NotFoundError):
    code = "user_not_found"
    message = "User not found"


class EmailAlreadyExists(ConflictError):
    code = "email_already_exists"
    message = "User with this email already exists"