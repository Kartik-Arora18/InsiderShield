
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db_session
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate


router = APIRouter(prefix="/employees", tags=["employees"])


@router.post(
    "",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("admin", "analyst")),
):
    values = data.model_dump()
    values["email"] = str(data.email).lower()

    employee = Employee(
        organization_id=user.organization_id,
        **values,
    )

    db.add(employee)

    try:
        await db.commit()
        await db.refresh(employee)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee code or email already exists in this organization",
        )

    return employee


@router.get("", response_model=list[EmployeeRead])
async def list_employees(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Employee)
        .where(Employee.organization_id == user.organization_id)
        .order_by(Employee.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(result.scalars().all())


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.organization_id == user.organization_id,
        )
    )

    employee = result.scalar_one_or_none()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return employee


@router.patch("/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    employee_id: UUID,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("admin", "analyst")),
):
    result = await db.execute(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.organization_id == user.organization_id,
        )
    )

    employee = result.scalar_one_or_none()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("email"):
        update_data["email"] = str(update_data["email"]).lower()

    for key, value in update_data.items():
        setattr(employee, key, value)

    try:
        await db.commit()
        await db.refresh(employee)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee email already exists in this organization",
        )

    return employee
