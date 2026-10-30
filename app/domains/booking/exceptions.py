from app.core.exceptions import BadRequestError, ConflictError, NotFoundError


class BookingNotFound(NotFoundError):
    detail = "Запись не найдена"


class BookingConflict(ConflictError):
    detail = "Зал уже занят в это время"


class BookingInvalid(BadRequestError):
    detail = "Некорректная запись"


class BookingStateError(ConflictError):
    detail = "Недопустимое действие для текущего статуса записи"
