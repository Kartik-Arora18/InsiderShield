from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    employee_id: UUID
    risk_score: float = Field(ge=0, le=100)
    severity: str
    status: str
    title: str
    description: str
    detection_count: int
    contributing_factors: dict
    created_at: datetime
    updated_at: datetime


class AlertStatusUpdate(BaseModel):
    status: str = Field(pattern="^(acknowledged|resolved)$")
