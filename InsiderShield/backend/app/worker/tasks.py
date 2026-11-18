
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert

from app.db.session import AsyncSessionLocal

from app.models.activity_event import ActivityEvent
from app.models.activity_feature import ActivityFeature
from app.models.anomaly_detection import AnomalyDetection
from app.models.outbox_message import OutboxMessage

from app.services.feature_engineering import extract_features
from app.services.baseline_service import update_employee_baseline
from app.services.anomaly_detection_service import detect_anomaly
from app.services.risk_scoring_service import calculate_employee_risk
from app.services.alert_service import generate_or_update_alert

from app.worker.celery_app import celery_app


logger = logging.getLogger(__name__)

STALE_MESSAGE_MINUTES = 5

WARMUP_MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
WARMUP_OFF_HOURS_DOWNLOAD_BYTES = 10 * 1024 * 1024
WARMUP_MAX_EVENTS_PER_HOUR = 10

MODEL_VERSION = "2.0.0"


def evaluate_warmup_activity(feature):
    """
    Apply conservative rule-based checks when insufficient
    trusted history exists for Isolation Forest.

    These rules are provisional safety guardrails, not
    statistically learned anomaly predictions.
    """

    reasons = []

    if feature.download_size_bytes > WARMUP_MAX_DOWNLOAD_BYTES:
        reasons.append("download_exceeds_warmup_limit")

    if (
        feature.is_outside_business_hours
        and feature.download_size_bytes
        > WARMUP_OFF_HOURS_DOWNLOAD_BYTES
    ):
        reasons.append("large_download_outside_business_hours")

    if feature.events_last_hour >= WARMUP_MAX_EVENTS_PER_HOUR:
        reasons.append("unusually_high_hourly_activity")

    return reasons


async def _dispatch_pending() -> int:
    count = 0
    now = datetime.now(timezone.utc)
    stale_before = now - timedelta(minutes=STALE_MESSAGE_MINUTES)

    async with AsyncSessionLocal() as db:
        async with db.begin():
            result = await db.execute(
                select(OutboxMessage)
                .where(
                    or_(
                        (
                            (OutboxMessage.status == "pending")
                            & (OutboxMessage.available_at <= now)
                        ),
                        (
                            (OutboxMessage.status == "published")
                            & (OutboxMessage.dispatched_at <= stale_before)
                        ),
                    )
                )
                .order_by(OutboxMessage.created_at)
                .limit(100)
                .with_for_update(skip_locked=True)
            )

            for message in result.scalars().all():
                celery_app.send_task(
                    "app.worker.tasks.process_outbox_message",
                    args=[str(message.id)],
                )

                message.status = "published"
                message.dispatched_at = now
                count += 1

    return count


@celery_app.task(name="app.worker.tasks.dispatch_outbox")
def dispatch_outbox() -> int:
    count = asyncio.run(_dispatch_pending())

    if count:
        logger.info(
            "Dispatched or recovered %s outbox messages",
            count,
        )

    return count


async def _record_warmup_anomaly(db, event, feature, reasons):
    """
    Persist a rule-based detection for suspicious activity
    encountered before sufficient ML history exists.
    """

    explanation = {
        "reasons": reasons,
        "model_version": MODEL_VERSION,
        "detection_method": "warmup_rules",
        "note": (
            "This event was flagged by conservative warm-up "
            "rules because sufficient trusted ML history "
            "was unavailable. This is not an Isolation Forest result."
        ),
    }

    statement = insert(AnomalyDetection).values(
        event_id=event.id,
        organization_id=event.organization_id,
        employee_id=event.employee_id,
        anomaly_score=85.0,
        detection_method="warmup_rules",
        severity="high",
        explanation=explanation,
        model_version=MODEL_VERSION,
    )

    statement = statement.on_conflict_do_nothing(
        constraint="uq_anomaly_detection_event"
    )

    await db.execute(statement)

    return {
        "status": "anomaly_detected",
        "detection_method": "warmup_rules",
        "severity": "high",
        "anomaly_score": 85.0,
        "reasons": reasons,
        "model_version": MODEL_VERSION,
    }


async def _process_message(message_id: UUID, retry_number: int) -> str:

    async with AsyncSessionLocal() as db:
        async with db.begin():

            result = await db.execute(
                select(OutboxMessage)
                .where(OutboxMessage.id == message_id)
                .with_for_update()
            )

            message = result.scalar_one_or_none()

            if message is None:
                return "missing"

            if message.status == "completed":
                return "already_completed"

            if message.status == "dead":
                return "dead_lettered"

            event_result = await db.execute(
                select(ActivityEvent).where(
                    ActivityEvent.id == message.event_id
                )
            )

            event = event_result.scalar_one_or_none()

            if event is None:
                raise ValueError(
                    f"Activity event {message.event_id} was not found"
                )

            # 1. Extract behavioural features.
            feature = await extract_features(db, event)

            # 2. Evaluate using trusted historical activity.
            anomaly_result = await detect_anomaly(db, feature)

            anomaly_status = anomaly_result.get("status")

            # 3. Handle new employees or insufficient ML history.
            if anomaly_status == "insufficient_history":

                warmup_reasons = evaluate_warmup_activity(feature)

                if warmup_reasons:

                    feature.evaluation_status = "anomalous"

                    anomaly_result = await _record_warmup_anomaly(
                        db,
                        event,
                        feature,
                        warmup_reasons,
                    )

                    baseline_result = {
                        "status": "skipped_anomalous_event",
                    }

                else:

                    feature.evaluation_status = "warmup_accepted"

                    baseline = await update_employee_baseline(
                        db,
                        feature,
                    )

                    baseline_result = {
                        "status": "updated_during_warmup",
                        "sample_count": baseline.sample_count,
                        "event_type": baseline.event_type,
                    }

                    anomaly_result["status"] = "warmup_accepted"
                    anomaly_result["warmup_policy"] = (
                        "conservative_rule_based"
                    )

            # 4. Update baseline only for trusted normal activity.
            elif anomaly_status == "normal":

                feature.evaluation_status = "normal"

                baseline = await update_employee_baseline(
                    db,
                    feature,
                )

                baseline_result = {
                    "status": "updated",
                    "sample_count": baseline.sample_count,
                    "event_type": baseline.event_type,
                }

            # 5. Never allow anomalous activity into the baseline.
            elif anomaly_status == "anomaly_detected":

                feature.evaluation_status = "anomalous"

                baseline_result = {
                    "status": "skipped_anomalous_event",
                }

            else:

                raise ValueError(
                    f"Unexpected anomaly detection status: "
                    f"{anomaly_status}"
                )

            # 6. Calculate employee risk score.
            risk_result = await calculate_employee_risk(
                db,
                event.organization_id,
                event.employee_id,
            )

            # 7. Generate or update security alert.
            alert_result = await generate_or_update_alert(
                db,
                event.organization_id,
                event.employee_id,
            )

            # 8. Store complete processing result.
            message.processing_result = {
                "event_id": str(event.id),
                "organization_id": str(event.organization_id),
                "employee_id": str(event.employee_id),
                "event_type": event.event_type,
                "source": event.source,
                "occurred_at": event.occurred_at.isoformat(),
                "received_at": (
                    event.received_at.isoformat()
                    if event.received_at
                    else None
                ),
                "payload_keys": sorted(event.event_data.keys()),
                "payload": event.event_data,

                "behavioral_analysis": {
                    "feature_id": str(feature.id),
                    "hour_of_day": feature.hour_of_day,
                    "day_of_week": feature.day_of_week,
                    "is_weekend": feature.is_weekend,
                    "outside_business_hours": (
                        feature.is_outside_business_hours
                    ),
                    "download_size_bytes": feature.download_size_bytes,
                    "events_last_hour": feature.events_last_hour,
                    "events_last_24h": feature.events_last_24h,
                    "evaluation_status": feature.evaluation_status,
                },

                "baseline": baseline_result,
                "anomaly_detection": anomaly_result,
                "risk_assessment": risk_result,
                "alert": alert_result,
            }

            # 9. Mark processing complete.
            message.status = "completed"
            message.attempts = retry_number + 1
            message.processed_at = datetime.now(timezone.utc)
            message.last_error = None

            logger.info(
                "Event %s processed. ML status: %s, risk: %s, alert: %s",
                event.id,
                anomaly_status,
                risk_result["risk_score"],
                alert_result is not None,
            )

            return "completed"


@celery_app.task(
    bind=True,
    name="app.worker.tasks.process_outbox_message",
    max_retries=5,
    acks_late=True,
)
def process_outbox_message(self, message_id: str) -> str:

    try:

        return asyncio.run(
            _process_message(
                UUID(message_id),
                self.request.retries,
            )
        )

    except Exception as exc:

        logger.exception(
            "Processing failed for outbox message %s",
            message_id,
        )

        if self.request.retries >= self.max_retries:

            asyncio.run(
                _mark_dead(
                    UUID(message_id),
                    str(exc),
                    self.request.retries + 1,
                )
            )

            raise

        countdown = min(
            2 ** (self.request.retries + 1),
            60,
        )

        raise self.retry(
            exc=exc,
            countdown=countdown,
        )


async def _mark_dead(
    message_id: UUID,
    error: str,
    attempts: int,
) -> None:

    async with AsyncSessionLocal() as db:
        async with db.begin():

            result = await db.execute(
                select(OutboxMessage)
                .where(OutboxMessage.id == message_id)
                .with_for_update()
            )

            message = result.scalar_one_or_none()

            if message is not None and message.status != "completed":

                message.status = "dead"
                message.attempts = attempts
                message.last_error = error[:4000]


@celery_app.task(name="app.worker.tasks.retry_dead_letter")
def retry_dead_letter(message_id: str) -> str:

    async def _retry():

        async with AsyncSessionLocal() as db:
            async with db.begin():

                result = await db.execute(
                    select(OutboxMessage)
                    .where(
                        OutboxMessage.id == UUID(message_id)
                    )
                    .with_for_update()
                )

                message = result.scalar_one_or_none()

                if message is None:
                    return "missing"

                if message.status != "dead":
                    return f"not_dead:{message.status}"

                message.status = "pending"
                message.attempts = 0
                message.available_at = datetime.now(timezone.utc)
                message.dispatched_at = None
                message.processed_at = None
                message.last_error = None

        return "queued"

    return asyncio.run(_retry())
