import pytest
from pydantic import ValidationError
from app.schemas.activity_event import ActivityEventCreate
from app.schemas.employee import EmployeeCreate

def test_employee_schema():
    item = EmployeeCreate(employee_code="EMP-001", full_name="Test Employee", email="employee@example.com")
    assert item.employee_code == "EMP-001"

def test_event_requires_timezone():
    with pytest.raises(ValidationError):
        ActivityEventCreate(employee_id="00000000-0000-0000-0000-000000000001", idempotency_key="event-key-0001", event_type="file.download", occurred_at="2026-11-12T10:00:00")

def test_event_normalizes_timezone_to_utc():
    item = ActivityEventCreate(employee_id="00000000-0000-0000-0000-000000000001", idempotency_key="event-key-0002", event_type="file.download", occurred_at="2026-11-12T10:00:00+05:30")
    assert item.occurred_at.utcoffset().total_seconds() == 0
