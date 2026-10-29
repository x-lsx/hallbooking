from pydantic import BaseModel, ConfigDict, Field


class EventFormatShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class EventFormatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None = None


class EventFormatCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=255)
