from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class EmployeeCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    department: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, max_length=120)

class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    email: EmailStr | None = None
    department: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None

class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    employee_code: str
    full_name: str
    email: EmailStr
    department: str | None
    job_title: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
