
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.employee import Employee
from app.models.risk_score import RiskScore


ALERT_RISK_THRESHOLD = 60


async def generate_or_update_alert(
    db: AsyncSession,
    organization_id: UUID,
    employee_id: UUID,
) -> dict | None:
    result = await db.execute(
        select(RiskScore).where(
            RiskScore.organization_id == organization_id,
            RiskScore.employee_id == employee_id,
        )
    )
    risk = result.scalar_one_or_none()

    if risk is None or risk.risk_score < ALERT_RISK_THRESHOLD:
        return None

    employee_result = await db.execute(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.organization_id == organization_id,
        )
    )
    employee = employee_result.scalar_one_or_none()

    if employee is None:
        return None

    factors = risk.contributing_factors or {}

    values = {
        "organization_id": organization_id,
        "employee_id": employee_id,
        "risk_score": risk.risk_score,
        "severity": risk.risk_level,
        "status": "open",
        "title": f"{risk.risk_level.upper()} insider threat risk detected",
        "description": (
            f"Employee {employee.full_name} has an insider-threat "
            f"risk score of {risk.risk_score:.2f}."
        ),
        "detection_count": factors.get("detection_count", 0),
        "contributing_factors": factors,
    }

    statement = insert(Alert).values(**values)

    # Target only the partial unique index for open alerts.
    statement = statement.on_conflict_do_update(
        index_elements=[
            Alert.organization_id,
            Alert.employee_id,
        ],
        index_where=(Alert.status == "open"),
        set_={
            "risk_score": statement.excluded.risk_score,
            "severity": statement.excluded.severity,
            "title": statement.excluded.title,
            "description": statement.excluded.description,
            "detection_count": statement.excluded.detection_count,
            "contributing_factors": statement.excluded.contributing_factors,
            "updated_at": text("now()"),
        },
    ).returning(Alert.id)

    alert_result = await db.execute(statement)
    alert_id = alert_result.scalar_one_or_none()

    if alert_id is None:
        return None

    await db.flush()

    return {
        "alert_id": str(alert_id),
        "employee_id": str(employee_id),
        "risk_score": risk.risk_score,
        "severity": risk.risk_level,
        "status": "open",
    }
