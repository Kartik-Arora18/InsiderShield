
import math
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.models.activity_event import ActivityEvent
from app.models.activity_feature import ActivityFeature
from app.models.anomaly_detection import AnomalyDetection


MODEL_VERSION = "2.0.0"

MIN_TRAINING_SAMPLES = 20
MAX_TRAINING_SAMPLES = 500
TRAINING_WINDOW_DAYS = 30

TRUSTED_STATUSES = ("warmup_accepted", "normal")


def feature_vector(feature):
    """
    Transform activity into numerical model features.

    Log transformations reduce the impact of extreme
    download sizes and event counts.

    Cyclical encoding represents hour and weekday
    without artificial boundary distances.
    """

    hour_angle = 2.0 * math.pi * feature.hour_of_day / 24.0
    day_angle = 2.0 * math.pi * feature.day_of_week / 7.0

    return [
        math.sin(hour_angle),
        math.cos(hour_angle),
        math.sin(day_angle),
        math.cos(day_angle),
        float(feature.is_weekend),
        float(feature.is_outside_business_hours),
        math.log1p(max(0, feature.download_size_bytes)),
        math.log1p(max(0, feature.events_last_hour)),
        math.log1p(max(0, feature.events_last_24h)),
    ]


async def detect_anomaly(db, feature: ActivityFeature):
    """
    Train an employee-specific Isolation Forest using
    trusted historical activity.

    Only previously evaluated normal or provisionally
    accepted events are eligible for training.
    """

    current_event_result = await db.execute(
        select(ActivityEvent).where(
            ActivityEvent.id == feature.event_id
        )
    )
    current_event = current_event_result.scalar_one()

    cutoff = current_event.occurred_at - timedelta(
        days=TRAINING_WINDOW_DAYS
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
            ActivityFeature.event_id != feature.event_id,
            ActivityEvent.occurred_at >= cutoff,
            ActivityEvent.occurred_at < current_event.occurred_at,
        )
        .order_by(ActivityEvent.occurred_at.desc())
        .limit(MAX_TRAINING_SAMPLES)
    )

    historical = list(result.scalars().all())

    if len(historical) < MIN_TRAINING_SAMPLES:
        return {
            "status": "insufficient_history",
            "training_samples": len(historical),
            "required_samples": MIN_TRAINING_SAMPLES,
            "model_version": MODEL_VERSION,
        }

    training_data = [
        feature_vector(item)
        for item in historical
    ]

    current_vector = [
        feature_vector(feature)
    ]

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "isolation_forest",
                IsolationForest(
                    n_estimators=150,
                    contamination="auto",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    model.fit(training_data)

    prediction = int(model.predict(current_vector)[0])

    decision_score = float(
        model.decision_function(current_vector)[0]
    )

    # Heuristic ranking score, not a probability.
    anomaly_score = max(
        0.0,
        min(100.0, 50.0 - decision_score * 100.0),
    )

    if prediction != -1:
        feature.evaluation_status = "normal"

        return {
            "status": "normal",
            "anomaly_score": round(anomaly_score, 2),
            "training_samples": len(historical),
            "model_version": MODEL_VERSION,
        }

    if anomaly_score >= 75:
        severity = "high"
    elif anomaly_score >= 60:
        severity = "medium"
    else:
        severity = "low"

    feature.evaluation_status = "anomalous"

    explanation = {
        "reasons": [
            {
                "feature": "download_size_bytes",
                "value": feature.download_size_bytes,
            },
            {
                "feature": "events_last_hour",
                "value": feature.events_last_hour,
            },
            {
                "feature": "events_last_24h",
                "value": feature.events_last_24h,
            },
            {
                "feature": "outside_business_hours",
                "value": feature.is_outside_business_hours,
            },
        ],
        "training_samples": len(historical),
        "decision_score": decision_score,
        "model_version": MODEL_VERSION,
        "note": (
            "Isolation Forest flagged this event as anomalous. "
            "Listed values are contextual signals, not individually "
            "proven causes. Anomaly score is not a probability."
        ),
    }

    statement = insert(AnomalyDetection).values(
        event_id=feature.event_id,
        organization_id=feature.organization_id,
        employee_id=feature.employee_id,
        anomaly_score=round(anomaly_score, 2),
        detection_method="isolation_forest",
        severity=severity,
        explanation=explanation,
        model_version=MODEL_VERSION,
    )

    statement = statement.on_conflict_do_nothing(
        constraint="uq_anomaly_detection_event"
    )

    await db.execute(statement)

    return {
        "status": "anomaly_detected",
        "anomaly_score": round(anomaly_score, 2),
        "severity": severity,
        "training_samples": len(historical),
        "model_version": MODEL_VERSION,
    }
