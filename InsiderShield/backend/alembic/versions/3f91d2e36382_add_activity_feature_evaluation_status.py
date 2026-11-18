
from alembic import op
import sqlalchemy as sa


revision = "3f91d2e36382"
down_revision = "0005_behavioral_analytics"
branch_labels = None
depends_on = None


def upgrade():
    # Add evaluation status to existing activity features.
    # Existing records safely receive "pending".
    op.add_column(
        "activity_features",
        sa.Column(
            "evaluation_status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
    )

    # Restrict values to the supported evaluation states.
    op.create_check_constraint(
        "ck_activity_features_evaluation_status",
        "activity_features",
        "evaluation_status IN "
        "('pending', 'warmup_accepted', 'normal', 'anomalous')",
    )

    # Index trusted-history lookups.
    op.create_index(
        "ix_features_trusted_history",
        "activity_features",
        [
            "organization_id",
            "employee_id",
            "event_type",
            "evaluation_status",
        ],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_features_trusted_history",
        table_name="activity_features",
    )

    op.drop_constraint(
        "ck_activity_features_evaluation_status",
        "activity_features",
        type_="check",
    )

    op.drop_column(
        "activity_features",
        "evaluation_status",
    )
