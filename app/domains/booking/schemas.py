from datetime import datetime, timedelta

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import BookingStatus, SourceType

MAX_CALENDAR_RANGE = timedelta(days=62)

class BookingFilter(BaseModel):
    start_at: AwareDatetime
    end_at: AwareDatetime
 
    @model_validator(mode="after")
    def validate_period(self):
        if self.start_at >= self.end_at:
            raise ValueError("Начало периода должно быть раньше конца")
        if self.end_at - self.start_at > MAX_CALENDAR_RANGE:
            raise ValueError("Период не может быть больше 62 дней")
        return self
 
 
class BookingCalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id: int
    title: str
    start_at: AwareDatetime
    end_at: AwareDatetime
    status: BookingStatus


class BookingListFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statuses: list[BookingStatus] = Field(default_factory=list, max_length=4)
    room_id: int | None = Field(default=None, gt=0)
    start_at: AwareDatetime | None = None
    end_at: AwareDatetime | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_period(self) -> "BookingListFilter":
        if self.start_at is not None and self.end_at is not None:
            if self.end_at <= self.start_at:
                raise ValueError("Начало периода должно быть раньше конца")
        return self

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
 
 
class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id: int
    title: str
    requester_first_name: str
    requester_last_name: str
    requester_middle_name: str | None
    requester_phone: str
    created_by_id: int
    room_id: int
    event_id: int
    department_id: int
    decided_by_id: int | None
    source: SourceType
    status: BookingStatus
    attendees_count: int
    is_public: bool
    start_at: AwareDatetime
    end_at: AwareDatetime
    reject_reason: str | None
    created_at: datetime
 
 
class BookingBase(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    event_format_id: int
    attendees_count: int = Field(gt=0)
    is_public: bool = True
    start_at: AwareDatetime
    end_at: AwareDatetime
 
    @model_validator(mode="after")
    def validate_period(self):
        if self.end_at <= self.start_at:
            raise ValueError("Окончание должно быть позже начала")
        return self
 
 
class BookingOnlineCreate(BookingBase):
    room_id: int
    department_id: int | None = None
 
 
class BookingOfflineCreate(BookingBase):
    department_id: int
    requester_first_name: str = Field(min_length=1, max_length=128)
    requester_last_name: str = Field(min_length=1, max_length=128)
    requester_middle_name: str | None = Field(default=None, max_length=128)
    requester_phone: str = Field(min_length=5, max_length=20)

    @field_validator("requester_middle_name", mode="before")
    @classmethod
    def normalize_middle_name(cls, value: str | None) -> str | None:
        return value.strip() or None if isinstance(value, str) else value
 
 
class BookingReject(BaseModel):
    reject_reason: str = Field(min_length=1, max_length=512)
