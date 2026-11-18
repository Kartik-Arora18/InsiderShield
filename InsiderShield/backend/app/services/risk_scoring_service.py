
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anomaly_detection import AnomalyDetection
from app.models.risk_score import RiskScore


RISK_WINDOW_DAYS = 30

SEVERITY_VALUES = {
    "low": 35,
    "medium": 65,
    "high": 85,
    "critical": 100,
}


def get_risk_level(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def calculate_risk_components(
    detections: list[AnomalyDetection],
    now: datetime,
) -> dict:
    if not detections:
        return {
            "anomaly_score": 0.0,
            "severity_score": 0.0,
            "frequency_score": 0.0,
            "recency_score": 0.0,
            "total_score": 0.0,
            "detection_count": 0,
        }

    # Use the strongest anomaly score in the window.
    anomaly_score = max(
        max(0.0, min(float(d.anomaly_score), 100.0))
        for d in detections
    )

    # Use the strongest severity in the window.
    severity_score = max(
        SEVERITY_VALUES.get(d.severity.lower(), 35)
        for d in detections
    )

    # Five or more detections reach the frequency component cap.
    frequency_score = min(len(detections) / 5 * 100, 100)

    latest_detection = max(d.detected_at for d in detections)
    age = max(
        0.0,
        (now - latest_detection).total_seconds() / 3600,
    )

    if age <= 24:
        recency_score = 100
    elif age <= 24 * 7:
        recency_score = 75
    else:
        recency_score = 40

    total_score = (
        anomaly_score * 0.50
        + severity_score * 0.25
        + frequency_score * 0.15
        + recency_score * 0.10
    )

    return {
        "anomaly_score": round(anomaly_score, 2),
        "severity_score": round(severity_score, 2),
        "frequency_score": round(frequency_score, 2),
        "recency_score": round(recency_score, 2),
        "total_score": round(min(total_score, 100), 2),
        "detection_count": len(detections),
    }


async def calculate_employee_risk(
    db: AsyncSession,
    organization_id: UUID,
    employee_id: UUID,
) -> dict:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=RISK_WINDOW_DAYS)

    result = await db.execute(
        select(AnomalyDetection).where(
            AnomalyDetection.organization_id == organization_id,
            AnomalyDetection.employee_id == employee_id,
            AnomalyDetection.detected_at >= cutoff,
            AnomalyDetection.detected_at <= now,
        )
    )

    detections = list(result.scalars().all())

    components = calculate_risk_components(detections, now)
    score = components["total_score"]
    risk_level = get_risk_level(score)

    values = {
        "organization_id": organization_id,
        "employee_id": employee_id,
        "risk_score": score,
        "risk_level": risk_level,
        "contributing_factors": components,
        "last_calculated_at": now,
    }

    statement = insert(RiskScore).values(**values)

    statement = statement.on_conflict_do_update(
        constraint="uq_risk_score_org_employee",
        set_={
            "risk_score": statement.excluded.risk_score,
            "risk_level": statement.excluded.risk_level,
            "contributing_factors": statement.excluded.contributing_factors,
            "last_calculated_at": statement.excluded.last_calculated_at,
        },
    )

    await db.execute(statement)
    await db.flush()

    return {
        "employee_id": str(employee_id),
        "risk_score": score,
        "risk_level": risk_level,
        "contributing_factors": components,
    }
