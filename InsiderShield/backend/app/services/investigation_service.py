
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.employee import Employee
from app.models.investigation import (
    Investigation,
    InvestigationAlert,
    InvestigationAudit,
)
from app.models.user import User


async def get_investigation(
    db: AsyncSession,
    organization_id: UUID,
    investigation_id: UUID,
) -> Investigation:
    result = await db.execute(
        select(Investigation).where(
            Investigation.id == investigation_id,
            Investigation.organization_id == organization_id,
        )
    )
    investigation = result.scalar_one_or_none()

    if investigation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found",
        )

    return investigation


async def validate_employee(
    db: AsyncSession,
    organization_id: UUID,
    employee_id: UUID | None,
):
    if employee_id is None:
        return

    result = await db.execute(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.organization_id == organization_id,
        )
    )

    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )


async def validate_assignee(
    db: AsyncSession,
    organization_id: UUID,
    assigned_to: UUID | None,
):
    if assigned_to is None:
        return

    result = await db.execute(
        select(User).where(
            User.id == assigned_to,
            User.organization_id == organization_id,
            User.is_active.is_(True),
            User.role.in_(["admin", "analyst"]),
        )
    )

    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned investigator must be an active admin or analyst in your organization",
        )


async def add_audit(
    db: AsyncSession,
    investigation_id: UUID,
    actor_id: UUID,
    action: str,
    details: dict | None = None,
):
    audit = InvestigationAudit(
        investigation_id=investigation_id,
        actor_id=actor_id,
        action=action,
        details=details or {},
    )

    db.add(audit)


async def create_investigation(
    db: AsyncSession,
    user: User,
    data,
) -> Investigation:
    await validate_employee(
        db, user.organization_id, data.employee_id
    )

    await validate_assignee(
        db, user.organization_id, data.assigned_to
    )

    investigation = Investigation(
        organization_id=user.organization_id,
        employee_id=data.employee_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        assigned_to=data.assigned_to,
        created_by=user.id,
    )

    db.add(investigation)
    await db.flush()

    await add_audit(
        db,
        investigation.id,
        user.id,
        "investigation_created",
        {"title": investigation.title},
    )

    await db.commit()
    await db.refresh(investigation)

    return investigation


async def update_investigation(
    db: AsyncSession,
    user: User,
    investigation_id: UUID,
    data,
) -> Investigation:
    investigation = await get_investigation(
        db, user.organization_id, investigation_id
    )

    if investigation.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Closed investigations cannot be modified",
        )

    changes = data.model_dump(exclude_unset=True)

    if "employee_id" in changes:
        await validate_employee(
            db, user.organization_id, changes["employee_id"]
        )

    if "assigned_to" in changes:
        await validate_assignee(
            db, user.organization_id, changes["assigned_to"]
        )

    if changes.get("status") == "closed":
        from sqlalchemy import func

        investigation.closed_at = await db.scalar(select(func.now()))

    elif changes.get("status") in ("open", "in_progress"):
        investigation.closed_at = None

    for field, value in changes.items():
        setattr(investigation, field, value)

    await add_audit(
        db,
        investigation.id,
        user.id,
        "investigation_updated",
        changes,
    )

    try:
        await db.commit()
        await db.refresh(investigation)
    except Exception:
        await db.rollback()
        raise

    return investigation


async def link_alert(
    db: AsyncSession,
    user: User,
    investigation_id: UUID,
    alert_id: UUID,
):
    investigation = await get_investigation(
        db, user.organization_id, investigation_id
    )

    if investigation.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot link alerts to a closed investigation",
        )

    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id == user.organization_id,
        )
    )

    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    existing = await db.get(
        InvestigationAlert,
        (investigation_id, alert_id),
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alert is already linked to this investigation",
        )

    link = InvestigationAlert(
        investigation_id=investigation_id,
        alert_id=alert_id,
        linked_by=user.id,
    )

    db.add(link)

    await add_audit(
        db,
        investigation.id,
        user.id,
        "alert_linked",
        {"alert_id": str(alert_id)},
    )

    try:
        await db.commit()
        await db.refresh(link)
    except Exception:
        await db.rollback()
        raise

    return link
