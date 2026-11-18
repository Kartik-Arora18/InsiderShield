
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db_session
from app.models.investigation import (
    Investigation,
    InvestigationAlert,
    InvestigationAudit,
)
from app.models.user import User
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationUpdate,
    InvestigationRead,
    InvestigationAlertLink,
    InvestigationAlertRead,
    InvestigationAuditRead,
)
from app.services.investigation_service import (
    create_investigation,
    get_investigation,
    link_alert,
    update_investigation,
)

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationRead, status_code=201)
async def create_case(
    data: InvestigationCreate,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("admin", "analyst")),
):
    return await create_investigation(db, user, data)


@router.get("", response_model=list[InvestigationRead])
async def list_cases(
    case_status: str | None = Query(
        default=None,
        alias="status",
        pattern="^(open|in_progress|closed)$",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = select(Investigation).where(
        Investigation.organization_id == user.organization_id
    )

    if case_status:
        query = query.where(Investigation.status == case_status)

    result = await db.execute(
        query.order_by(Investigation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(result.scalars().all())


@router.get("/{investigation_id}", response_model=InvestigationRead)
async def get_case(
    investigation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    return await get_investigation(
        db, user.organization_id, investigation_id
    )


@router.patch("/{investigation_id}", response_model=InvestigationRead)
async def update_case(
    investigation_id: UUID,
    data: InvestigationUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("admin", "analyst")),
):
    return await update_investigation(
        db, user, investigation_id, data
    )


@router.post(
    "/{investigation_id}/alerts",
    response_model=InvestigationAlertRead,
    status_code=201,
)
async def add_alert(
    investigation_id: UUID,
    data: InvestigationAlertLink,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("admin", "analyst")),
):
    return await link_alert(
        db, user, investigation_id, data.alert_id
    )


@router.get(
    "/{investigation_id}/alerts",
)
async def list_linked_alerts(
    investigation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    await get_investigation(
        db, user.organization_id, investigation_id
    )

    result = await db.execute(
        select(InvestigationAlert).where(
            InvestigationAlert.investigation_id == investigation_id
        )
    )

    return list(result.scalars().all())


@router.get(
    "/{investigation_id}/audit",
    response_model=list[InvestigationAuditRead],
)
async def list_audit_history(
    investigation_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    await get_investigation(
        db, user.organization_id, investigation_id
    )

    result = await db.execute(
        select(InvestigationAudit)
        .where(
            InvestigationAudit.investigation_id == investigation_id
        )
        .order_by(InvestigationAudit.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(result.scalars().all())
