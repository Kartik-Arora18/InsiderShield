"""correct alert lifecycle database constraint"""

from alembic import op
import sqlalchemy as sa


revision = "e6d6da2d9b19"
down_revision = "12454b0ccca2"
branch_labels = None
depends_on = None


def upgrade():
    # Remove the old constraint that incorrectly restricts
    # historical alerts with the same status.
    op.drop_constraint(
        "uq_alert_org_employee_status",
        "alerts",
        type_="unique",
    )

    # Allow only one OPEN alert per employee.
    # Acknowledged and resolved alerts can have multiple records.
    op.create_index(
        "uq_alert_one_open_per_employee",
        "alerts",
        ["organization_id", "employee_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )


def downgrade():
    op.drop_index(
        "uq_alert_one_open_per_employee",
        table_name="alerts",
    )

    op.create_unique_constraint(
        "uq_alert_org_employee_status",
        "alerts",
        ["organization_id", "employee_id", "status"],
    )