from datetime import time

from pydantic import BaseModel, ConfigDict, Field


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
    
class RoomCreate(BaseModel):
    building_id: int
    organization: str | None
    number: str
    name: str | None
    capacity: int
    type: str
    open_from: time | None = None
    open_until: time | None = None
    is_active: bool | None = True

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
    organization: str | None = None
    number: str | None = None
    name: str | None = None
    capacity: int | None = None
    type: str | None = None
    open_from: time | None = None
    open_until: time | None = None
    is_active: bool | None = None
    
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