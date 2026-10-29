from datetime import AwareDatetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import BookingStatus, SourceType


class BookingFullResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    requster_first_name: str
    requster_last_name: str
    requster_middle_name: str
    requster_phone: str
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


class BookingСalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    start_at: AwareDatetime
    end_at: AwareDatetime


class BookingFilter(BaseModel):
    start_at: AwareDatetime
    end_at: AwareDatetime

    @model_validator(mode="after")
    def validate_period(self):
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.start_at >= self.end_at
        ):
            raise ValueError("start_at must be earlier than end_at")

        return self


class BookingUserCreate(BaseModel):
    title: str
    requster_first_name: str
    requster_last_name: str
    requster_middle_name: str
    requster_phone: str
    created_by_id: int
    room_id: int
    event_id: int
    department_id: int
    source: SourceType
    attendees_count: int
    is_public: bool
    start_at: AwareDatetime
    end_at: AwareDatetime
