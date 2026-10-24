
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Password = Annotated[str, Field(min_length=8, max_length=128)]

class UserLogin(BaseModel):
    email: EmailStr
    password: str  # при логине длину не проверяем, только при создании

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()


class UserCreate(BaseModel):
    email: EmailStr
    phone_number: str
    password: Password
    first_name: Name | None = None
    last_name: Name | None = None

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "johndoe@example.com",
                    "phone_number": "+1234567890",
                    "password": "secret1234",
                    "first_name": "John",
                    "last_name": "Doe",
                }
            ]
        }
    }


class ChangePassword(BaseModel):
    old_password: str
    new_password: Password


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str
    new_password: Password