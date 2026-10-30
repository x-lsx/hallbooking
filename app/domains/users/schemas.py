from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

from app.domains.departments.schemas import DepartmentResponse

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]

class UserUpdate(BaseModel):
    first_name: Name | None = None
    last_name: Name | None = None
    middle_name: Name | None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str | None
    last_name: str | None
    middle_name: str | None
    phone_number: str 
    department: DepartmentResponse
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime