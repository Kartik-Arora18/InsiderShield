from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RiskScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    employee_id: UUID
    risk_score: float = Field(ge=0, le=100)
    risk_level: str
    contributing_factors: dict
    last_calculated_at: datetime
