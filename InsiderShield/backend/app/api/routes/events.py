from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db_session
from app.models.activity_event import ActivityEvent
from app.models.employee import Employee
from app.models.outbox_message import OutboxMessage
from app.models.user import User
from app.schemas.activity_event import ActivityEventBulkCreate, ActivityEventCreate, ActivityEventRead, EventIngestResult

router = APIRouter(prefix="/events", tags=["activity events"])

async def _ingest_one(data: ActivityEventCreate, user: User, db: AsyncSession):
    employee_result = await db.execute(select(Employee.id).where(
        Employee.id == data.employee_id,
        Employee.organization_id == user.organization_id,
        Employee.is_active.is_(True)))
    if employee_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Active employee not found in your organization")
    stmt = insert(ActivityEvent).values(
        organization_id=user.organization_id, employee_id=data.employee_id,
        idempotency_key=data.idempotency_key, event_type=data.event_type,
        source=data.source, occurred_at=data.occurred_at, event_data=data.event_data,
    ).on_conflict_do_nothing(constraint="uq_events_org_idempotency").returning(ActivityEvent.id)
    result = await db.execute(stmt)
    event_id = result.scalar_one_or_none()
    if event_id is not None:
        db.add(OutboxMessage(event_id=event_id, status="pending"))
    return event_id

@router.post("", response_model=EventIngestResult, status_code=202)
async def ingest_event(data: ActivityEventCreate, db: AsyncSession = Depends(get_db_session),
                       user: User = Depends(require_roles("admin", "analyst"))):
    event_id = await _ingest_one(data, user, db)
    await db.commit()
    return EventIngestResult(accepted=1 if event_id else 0, duplicates=0 if event_id else 1,
                             event_ids=[event_id] if event_id else [])

@router.post("/bulk", response_model=EventIngestResult, status_code=202)
async def ingest_events_bulk(data: ActivityEventBulkCreate, db: AsyncSession = Depends(get_db_session),
                             user: User = Depends(require_roles("admin", "analyst"))):
    ids, duplicates = [], 0
    try:
        for event in data.events:
            event_id = await _ingest_one(event, user, db)
            if event_id:
                ids.append(event_id)
            else:
                duplicates += 1
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return EventIngestResult(accepted=len(ids), duplicates=duplicates, event_ids=ids)

@router.get("", response_model=list[ActivityEventRead])
async def list_events(employee_id: UUID | None = None, limit: int = 50, offset: int = 0,
                      db: AsyncSession = Depends(get_db_session), user: User = Depends(get_current_user)):
    if limit < 1 or limit > 200 or offset < 0:
        raise HTTPException(status_code=422, detail="Invalid pagination")
    query = select(ActivityEvent).where(ActivityEvent.organization_id == user.organization_id)
    if employee_id:
        query = query.where(ActivityEvent.employee_id == employee_id)
    result = await db.execute(query.order_by(ActivityEvent.occurred_at.desc()).limit(limit).offset(offset))
    return list(result.scalars().all())
