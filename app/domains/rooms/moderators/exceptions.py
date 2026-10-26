from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
 
 
class ModeratorNotFound(NotFoundError):
    detail = "Назначение модератора не найдено"
 
 
class ModeratorAlreadyAssigned(ConflictError):
    detail = "Пользователь уже назначен модератором этого зала"
 
 
class ModeratorInvalid(BadRequestError):
    """Нарушено бизнес-правило назначения; текст передаётся при создании."""
    detail = "Некорректное назначение модератора"