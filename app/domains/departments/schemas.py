from pydantic import BaseModel, ConfigDict, Field, model_validator

class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    
class DepartmentCreate(BaseModel):
    name: str