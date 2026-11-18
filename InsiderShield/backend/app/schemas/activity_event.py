from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ActivityEventCreate(BaseModel):
    employee_id: UUID
    idempotency_key: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    event_type: str = Field(min_length=2, max_length=80, pattern=r"^[a-z][a-z0-9_.-]*$")
    source: str = Field(default="api", min_length=2, max_length=80)
    occurred_at: datetime
    event_data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def timezone_required(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value.astimezone(timezone.utc)

class ActivityEventBulkCreate(BaseModel):
    events: list[ActivityEventCreate] = Field(min_length=1, max_length=500)

class ActivityEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    employee_id: UUID
    idempotency_key: str
    event_type: str
    source: str
    occurred_at: datetime
    event_data: dict[str, Any]
    received_at: datetime

class EventIngestResult(BaseModel):
    accepted: int
    duplicates: int
    event_ids: list[UUID]
