
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    employee_id: UUID | None = None
    assigned_to: UUID | None = None
    priority: str = Field(
        default="medium",
        pattern="^(low|medium|high|critical)$",
    )


class InvestigationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    assigned_to: UUID | None = None
    priority: str | None = Field(
        default=None,
        pattern="^(low|medium|high|critical)$",
    )
    status: str | None = Field(
        default=None,
        pattern="^(open|in_progress|closed)$",
    )


class InvestigationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    employee_id: UUID | None
    title: str
    description: str | None
    status: str
    priority: str
    assigned_to: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None


class InvestigationAlertLink(BaseModel):
    alert_id: UUID


class InvestigationAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    investigation_id: UUID
    alert_id: UUID
    linked_at: datetime
    linked_by: UUID | None


class InvestigationAuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investigation_id: UUID
    actor_id: UUID | None
    action: str
    details: dict
    created_at: datetime
