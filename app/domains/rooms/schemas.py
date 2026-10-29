from datetime import time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.event_format.schemas import EventFormatShort


class BuildingCreate(BaseModel):
    number: str
    name: str | None = None
    address: str
    
class BuildingUpdate(BaseModel):
    number: str | None = None
    name: str | None = None
    address: str | None = None
    
class BuildingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    name: str | None
    address: str | None

class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    building: BuildingResponse
    organization: str | None
    number: str
    name: str | None
    capacity: int
    type: str
    open_from: time
    open_until: time
    is_active: bool
    event_formats: list[EventFormatShort] = []
    
    
class RoomCreate(BaseModel):
    building_id: int
    organization: str | None = Field(default=None, max_length=128)
    number: str = Field(min_length=1, max_length=32)
    name: str | None = Field(default=None, max_length=128)
    capacity: int = Field(gt=0)
    type: str = Field(min_length=1, max_length=64)
    open_from: time = time(8, 0)
    open_until: time = time(20, 0)
    is_active: bool = True
    event_format_ids: list[int] = Field(default_factory=list)

class RoomCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    building_id: int
    organization: str | None
    number: str
    name: str | None
    capacity: int
    type: str
    open_from: time
    open_until: time
    is_active: bool

class RoomUpdate(BaseModel):
    building_id: int | None = None
    organization: str | None = Field(default=None, max_length=128)
    number: str | None = Field(default=None, min_length=1, max_length=32)
    name: str | None = Field(default=None, max_length=128)
    capacity: int | None = Field(default=None, gt=0)
    type: str | None = Field(default=None, min_length=1, max_length=64)
    open_from: time | None = None
    open_until: time | None = None
    is_active: bool | None = None
    event_format_ids: list[int] | None = None
       
    @model_validator(mode="after")
    def validate_patch(self):
        not_nullable = ("building_id", "number", "capacity", "type",
                        "open_from", "open_until", "is_active")
        for f in not_nullable:
            if f in self.model_fields_set and getattr(self, f) is None:
                raise ValueError(f"{f} не может быть null")
        if self.open_from and self.open_until and self.open_until <= self.open_from:
            raise ValueError("open_until должно быть позже open_from")
        return self
    
class RoomFilter(BaseModel):
    building_id: int | None = None
    capacity_min: int | None = None
    type: str | None = None
    formats_ids: list[int] = Field(default_factory=list)
    is_active: bool | None = True
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size