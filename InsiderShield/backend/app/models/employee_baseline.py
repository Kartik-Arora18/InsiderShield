import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmployeeBaseline(Base):
    __tablename__ = "employee_baselines"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "employee_id",
            "event_type",
            name="uq_employee_baseline_org_employee_type",
        ),
        Index(
            "ix_baselines_org_employee",
            "organization_id",
            "employee_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(String(80), nullable=False)

    sample_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    avg_download_size_bytes: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0"
    )

    std_download_size_bytes: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0"
    )

    avg_events_per_hour: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0"
    )

    std_events_per_hour: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0"
    )

    avg_events_per_day: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0"
    )

    std_events_per_day: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )