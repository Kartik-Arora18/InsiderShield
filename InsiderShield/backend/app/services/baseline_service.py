
import statistics
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.activity_event import ActivityEvent
from app.models.activity_feature import ActivityFeature
from app.models.employee_baseline import EmployeeBaseline


MAX_BASELINE_SAMPLES = 500
BASELINE_WINDOW_DAYS = 30

TRUSTED_STATUSES = {"warmup_accepted", "normal"}


async def update_employee_baseline(db, feature: ActivityFeature):
    """
    Recalculate an employee's behavioral baseline using
    only trusted historical activity.

    History is isolated by organization, employee and event type.
    Only the most recent 500 trusted events within 30 days are used.
    """

    if feature.evaluation_status not in TRUSTED_STATUSES:
        raise ValueError(
            "Cannot update baseline using an untrusted feature: "
            f"{feature.evaluation_status}"
        )

    event_result = await db.execute(
        select(ActivityEvent).where(
            ActivityEvent.id == feature.event_id
        )
    )
    current_event = event_result.scalar_one()

    cutoff = current_event.occurred_at - timedelta(
        days=BASELINE_WINDOW_DAYS
    )

    result = await db.execute(
        select(ActivityFeature)
        .join(
            ActivityEvent,
            ActivityEvent.id == ActivityFeature.event_id,
        )
        .where(
            ActivityFeature.organization_id == feature.organization_id,
            ActivityFeature.employee_id == feature.employee_id,
            ActivityFeature.event_type == feature.event_type,
            ActivityFeature.evaluation_status.in_(TRUSTED_STATUSES),
            ActivityEvent.occurred_at >= cutoff,
            ActivityEvent.occurred_at <= current_event.occurred_at,
            ActivityFeature.event_id != feature.event_id,
        )
        .order_by(ActivityEvent.occurred_at.desc())
        .limit(MAX_BASELINE_SAMPLES - 1)
    )

    historical_features = list(result.scalars().all())

    samples = historical_features + [feature]

    download_values = [
        float(item.download_size_bytes)
        for item in samples
    ]

    hourly_values = [
        float(item.events_last_hour + 1)
        for item in samples
    ]

    daily_values = [
        float(item.events_last_24h + 1)
        for item in samples
    ]

    def average(values):
        return statistics.mean(values) if values else 0.0

    def std_dev(values):
        return statistics.stdev(values) if len(values) > 1 else 0.0

    values = {
        "sample_count": len(samples),
        "avg_download_size_bytes": average(download_values),
        "std_download_size_bytes": std_dev(download_values),
        "avg_events_per_hour": average(hourly_values),
        "std_events_per_hour": std_dev(hourly_values),
        "avg_events_per_day": average(daily_values),
        "std_events_per_day": std_dev(daily_values),
    }

    statement = insert(EmployeeBaseline).values(
        organization_id=feature.organization_id,
        employee_id=feature.employee_id,
        event_type=feature.event_type,
        **values,
    )

    statement = statement.on_conflict_do_update(
        constraint="uq_employee_baseline_org_employee_type",
        set_=values,
    )

    await db.execute(statement)

    result = await db.execute(
        select(EmployeeBaseline).where(
            EmployeeBaseline.organization_id == feature.organization_id,
            EmployeeBaseline.employee_id == feature.employee_id,
            EmployeeBaseline.event_type == feature.event_type,
        )
    )

    return result.scalar_one()
