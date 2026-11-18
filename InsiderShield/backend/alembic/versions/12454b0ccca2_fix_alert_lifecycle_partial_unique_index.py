
"""fix alert lifecycle partial unique index

Revision ID: 12454b0ccca2
Revises: e02eb4d67635
Create Date: 2026-11-13 12:02:05.838796
"""

from alembic import op
import sqlalchemy as sa


revision = "12454b0ccca2"
down_revision = "e02eb4d67635"
branch_labels = None
depends_on = None


def upgrade():
    # Remove the old constraint that restricted historical alerts.
    op.drop_constraint(
        "uq_alert_org_employee_status",
        "alerts",
        type_="unique",
    )

    # Allow only one OPEN alert per employee per organization.
    # Acknowledged and resolved alerts can exist multiple times.
    op.create_index(
        "uq_alert_one_open_per_employee",
        "alerts",
        ["organization_id", "employee_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )


def downgrade():
    # Remove the partial unique index.
    op.drop_index(
        "uq_alert_one_open_per_employee",
        table_name="alerts",
    )

    # Restore the original constraint.
    # This can fail if multiple historical alerts share a status.
    op.create_unique_constraint(
        "uq_alert_org_employee_status",
        "alerts",
        ["organization_id", "employee_id", "status"],
    )
