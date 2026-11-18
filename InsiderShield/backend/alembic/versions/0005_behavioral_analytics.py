"""Add behavioral analytics and anomaly detection tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_behavioral_analytics"
down_revision = "0004_transactional_outbox"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "activity_features",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("hour_of_day", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("is_weekend", sa.Boolean(), nullable=False),
        sa.Column("is_outside_business_hours", sa.Boolean(), nullable=False),
        sa.Column("download_size_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("events_last_hour", sa.Integer(), server_default="0", nullable=False),
        sa.Column("events_last_24h", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["activity_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_activity_features_event"),
    )

    op.create_index(
        "ix_features_org_employee_time",
        "activity_features",
        ["organization_id", "employee_id", "created_at"],
    )

    op.create_table(
        "employee_baselines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("sample_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("avg_download_size_bytes", sa.Float(), server_default="0", nullable=False),
        sa.Column("std_download_size_bytes", sa.Float(), server_default="0", nullable=False),
        sa.Column("avg_events_per_hour", sa.Float(), server_default="0", nullable=False),
        sa.Column("std_events_per_hour", sa.Float(), server_default="0", nullable=False),
        sa.Column("avg_events_per_day", sa.Float(), server_default="0", nullable=False),
        sa.Column("std_events_per_day", sa.Float(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "employee_id",
            "event_type",
            name="uq_employee_baseline_org_employee_type",
        ),
    )

    op.create_index(
        "ix_baselines_org_employee",
        "employee_baselines",
        ["organization_id", "employee_id"],
    )

    op.create_table(
        "anomaly_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("detection_method", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model_version", sa.String(40), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["activity_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_anomaly_detection_event"),
    )

    op.create_index(
        "ix_anomalies_org_severity",
        "anomaly_detections",
        ["organization_id", "severity"],
    )

    op.create_index(
        "ix_anomalies_org_employee",
        "anomaly_detections",
        ["organization_id", "employee_id"],
    )


def downgrade():
    op.drop_index("ix_anomalies_org_employee", table_name="anomaly_detections")
    op.drop_index("ix_anomalies_org_severity", table_name="anomaly_detections")
    op.drop_table("anomaly_detections")

    op.drop_index("ix_baselines_org_employee", table_name="employee_baselines")
    op.drop_table("employee_baselines")

    op.drop_index("ix_features_org_employee_time", table_name="activity_features")
    op.drop_table("activity_features")