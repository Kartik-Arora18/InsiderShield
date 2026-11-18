from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func

from app.models.activity_event import ActivityEvent
from app.models.activity_feature import ActivityFeature


BUSINESS_START_HOUR = 9
BUSINESS_END_HOUR = 18


def extract_download_size(event_data: dict) -> int:
    """
    Extract download size from event payload.
    Supports common payload key names.
    """
    for key in (
        "download_size_bytes",
        "file_size_bytes",
        "bytes_downloaded",
    ):
        value = event_data.get(key)

        if value is not None:
            try:
                return max(0, int(value))
            except (TypeError, ValueError):
                return 0

    return 0


async def extract_features(db, event: ActivityEvent) -> ActivityFeature:
    """
    Convert an activity event into numerical behavioral features.
    """

    existing = await db.execute(
        select(ActivityFeature).where(
            ActivityFeature.event_id == event.id
        )
    )

    feature = existing.scalar_one_or_none()

    if feature:
        return feature

    occurred_at = event.occurred_at

    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)

    hour = occurred_at.hour
    day = occurred_at.weekday()

    one_hour_ago = occurred_at - timedelta(hours=1)
    one_day_ago = occurred_at - timedelta(hours=24)

    hourly_result = await db.execute(
        select(func.count(ActivityEvent.id)).where(
            ActivityEvent.organization_id == event.organization_id,
            ActivityEvent.employee_id == event.employee_id,
            ActivityEvent.occurred_at >= one_hour_ago,
            ActivityEvent.occurred_at <= occurred_at,
        )
    )

    daily_result = await db.execute(
        select(func.count(ActivityEvent.id)).where(
            ActivityEvent.organization_id == event.organization_id,
            ActivityEvent.employee_id == event.employee_id,
            ActivityEvent.occurred_at >= one_day_ago,
            ActivityEvent.occurred_at <= occurred_at,
        )
    )

    events_last_hour = max(0, hourly_result.scalar_one() - 1)
    events_last_24h = max(0, daily_result.scalar_one() - 1)

    feature = ActivityFeature(
        event_id=event.id,
        organization_id=event.organization_id,
        employee_id=event.employee_id,
        event_type=event.event_type,
        hour_of_day=hour,
        day_of_week=day,
        is_weekend=day >= 5,
        is_outside_business_hours=(
            hour < BUSINESS_START_HOUR
            or hour >= BUSINESS_END_HOUR
        ),
        download_size_bytes=extract_download_size(event.event_data),
        events_last_hour=events_last_hour,
        events_last_24h=events_last_24h,
    )

    db.add(feature)

    await db.flush()

    return feature