
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db_session
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertRead, AlertStatusUpdate


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
async def list_alerts(
    alert_status: str | None = Query(
        default=None,
        alias="status",
        pattern="^(open|acknowledged|resolved)$",
    ),
    severity: str | None = Query(
        default=None,
        pattern="^(low|medium|high|critical)$",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = select(Alert).where(
        Alert.organization_id == user.organization_id
    )

    if alert_status:
        query = query.where(Alert.status == alert_status)

    if severity:
        query = query.where(Alert.severity == severity)

    result = await db.execute(
        query.order_by(
            Alert.created_at.desc(),
            Alert.risk_score.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return list(result.scalars().all())


@router.get("/{alert_id}", response_model=AlertRead)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
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

    return alert


@router.patch(
    "/{alert_id}/status",
    response_model=AlertRead,
)
async def update_alert_status(
    alert_id: UUID,
    data: AlertStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("admin", "analyst")),
):
    result = await db.execute(
        select(Alert)
        .where(
            Alert.id == alert_id,
            Alert.organization_id == user.organization_id,
        )
        .with_for_update()
    )

    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    if alert.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A resolved alert cannot be modified",
        )

    if alert.status == data.status:
        return alert

    if alert.status == "open" and data.status != "acknowledged":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An open alert must be acknowledged before resolution",
        )

    if alert.status == "acknowledged" and data.status != "resolved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An acknowledged alert can only be resolved",
        )

    alert.status = data.status

    try:
        await db.commit()
        await db.refresh(alert)
    except Exception:
        await db.rollback()
        raise

    return alert
