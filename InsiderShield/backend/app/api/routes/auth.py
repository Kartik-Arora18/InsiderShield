from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.core.config import settings
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import LoginRequest, OrganizationRegistration, TokenResponse, UserRead
from app.services.auth_service import authenticate_user, issue_token, register_organization_and_admin

router = APIRouter(prefix="/auth", tags=["authentication"])


def user_payload(user: User) -> UserRead:
    return UserRead(
        id=str(user.id),
        organization_id=str(user.organization_id),
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


def token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=issue_token(user),
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_payload(user),
    )


@router.post("/register-organization", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_organization(
    data: OrganizationRegistration,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    _, user = await register_organization_and_admin(data, db)
    return token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db_session)) -> TokenResponse:
    user = await authenticate_user(
        organization_slug=data.organization_slug,
        email=str(data.email),
        password=data.password,
        db=db,
    )
    return token_response(user)


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)) -> UserRead:
    return user_payload(user)


@router.get("/admin-check")
async def admin_check(user: User = Depends(require_roles("admin"))) -> dict[str, str]:
    return {"message": "Admin access granted", "organization_id": str(user.organization_id)}
