from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.risk_score import RiskScore
from app.models.user import User
from app.schemas.risk_score import RiskScoreRead


router = APIRouter(prefix="/risk-scores", tags=["risk scores"])


@router.get("", response_model=list[RiskScoreRead])
async def list_risk_scores(
    risk_level: str | None = Query(
        default=None,
        pattern="^(low|medium|high|critical)$",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = select(RiskScore).where(
        RiskScore.organization_id == user.organization_id
    )

    if risk_level:
        query = query.where(RiskScore.risk_level == risk_level)

    result = await db.execute(
        query.order_by(
            RiskScore.risk_score.desc(),
            RiskScore.last_calculated_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return list(result.scalars().all())


@router.get("/{employee_id}", response_model=RiskScoreRead)
async def get_employee_risk_score(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RiskScore).where(
            RiskScore.employee_id == employee_id,
            RiskScore.organization_id == user.organization_id,
        )
    )

    risk_score = result.scalar_one_or_none()

    if risk_score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk score not found for this employee",
        )

    return risk_score
