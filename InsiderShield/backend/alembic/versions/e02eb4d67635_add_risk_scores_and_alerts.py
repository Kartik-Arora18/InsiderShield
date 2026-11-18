
"""add risk scores and alerts

Revision ID: e02eb4d67635
Revises: 3f91d2e36382
Create Date: 2026-11-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e02eb4d67635"
down_revision = "3f91d2e36382"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("detection_count", sa.Integer(), nullable=False),
        sa.Column(
            "contributing_factors",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "employee_id",
            "status",
            name="uq_alert_org_employee_status",
        ),
    )

    op.create_index(
        "ix_alerts_org_status_created",
        "alerts",
        ["organization_id", "status", "created_at"],
        unique=False,
    )

    op.create_table(
        "risk_scores",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("contributing_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("last_calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "employee_id",
            name="uq_risk_score_org_employee",
        ),
    )

    op.create_index(
        "ix_risk_scores_org_risk",
        "risk_scores",
        ["organization_id", "risk_level", "risk_score"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_risk_scores_org_risk", table_name="risk_scores")
    op.drop_table("risk_scores")

    op.drop_index("ix_alerts_org_status_created", table_name="alerts")
    op.drop_table("alerts")
