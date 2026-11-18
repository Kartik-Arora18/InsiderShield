from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.organization import Organization
from app.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def register_organization_and_admin(data, db: AsyncSession) -> tuple[Organization, User]:
    organization = Organization(name=data.organization_name.strip(), slug=data.organization_slug.lower())
    user = User(
        organization_id=organization.id,
        full_name=data.full_name.strip(),
        email=normalize_email(str(data.email)),
        password_hash=hash_password(data.password),
        role="admin",
        is_active=True,
    )
    db.add(organization)
    try:
        # Flush first so SQLAlchemy assigns the organization UUID before the user FK is set.
        await db.flush()
        user.organization_id = organization.id
        db.add(user)
        await db.commit()
        await db.refresh(organization)
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug is already registered",
        )
    return organization, user


async def authenticate_user(*, organization_slug: str, email: str, password: str, db: AsyncSession) -> User:
    query = (
        select(User)
        .join(Organization, User.organization_id == Organization.id)
        .where(
            Organization.slug == organization_slug.strip().lower(),
            User.email == normalize_email(email),
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect organization, email, or password")
    return user


def issue_token(user: User) -> str:
    return create_access_token(user_id=user.id, organization_id=user.organization_id, role=user.role)
