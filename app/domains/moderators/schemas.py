from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class UserShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id: int
    first_name: str
    last_name: str
    email: str
    
class ModeratorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    room_id: int
    user: UserShort
    valid_from: datetime
    valid_until: datetime | None
    
    
class ModeratorAssign(BaseModel):
    user_id: int
    valid_until: datetime | None = None
 
    @field_validator("valid_until")
    @classmethod
    def check_until(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        if v.tzinfo is None:
            raise ValueError("Укажите дату вместе с часовым поясом")
        if v <= datetime.now(UTC):
            raise ValueError("Дата окончания должна быть в будущем")
        return v