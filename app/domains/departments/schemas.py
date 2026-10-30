from pydantic import BaseModel, ConfigDict, Field, model_validator

class DepartmentResponse(BaseModel):
    id: int
    name: str