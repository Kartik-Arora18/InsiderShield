
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.dependencies import get_db_session
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models.alert import Alert
from app.models.employee import Employee
from app.models.investigation import Investigation
from app.models.organization import Organization
from app.models.user import User


@pytest_asyncio.fixture
async def api_context():
    test_url = make_url(settings.database_url).set(
        database="insidershield_test"
    )

    engine = create_async_engine(
        test_url,
        poolclass=NullPool,
        pool_pre_ping=True,
    )

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    organization_id = uuid.uuid4()
    foreign_organization_id = uuid.uuid4()

    admin_id = uuid.uuid4()
    analyst_id = uuid.uuid4()
    viewer_id = uuid.uuid4()
    foreign_user_id = uuid.uuid4()

    employee_id = uuid.uuid4()
    foreign_employee_id = uuid.uuid4()

    open_alert_id = uuid.uuid4()
    acknowledged_alert_id = uuid.uuid4()
    resolved_alert_id = uuid.uuid4()
    foreign_alert_id = uuid.uuid4()

    open_investigation_id = uuid.uuid4()
    closed_investigation_id = uuid.uuid4()
    foreign_investigation_id = uuid.uuid4()

    try:
        async with session_factory() as session:
            session.add_all([
                Organization(
                    id=organization_id,
                    name="InsiderShield Test Organization",
                    slug=f"test-org-{uuid.uuid4().hex[:12]}",
                ),
                Organization(
                    id=foreign_organization_id,
                    name="Foreign Test Organization",
                    slug=f"foreign-org-{uuid.uuid4().hex[:12]}",
                ),
            ])

            await session.flush()

            session.add_all([
                User(
                    id=admin_id,
                    organization_id=organization_id,
                    full_name="Test Admin",
                    email=f"admin-{uuid.uuid4().hex[:8]}@example.com",
                    password_hash="test-password-hash",
                    role="admin",
                    is_active=True,
                ),
                User(
                    id=analyst_id,
                    organization_id=organization_id,
                    full_name="Test Analyst",
                    email=f"analyst-{uuid.uuid4().hex[:8]}@example.com",
                    password_hash="test-password-hash",
                    role="analyst",
                    is_active=True,
                ),
                User(
                    id=viewer_id,
                    organization_id=organization_id,
                    full_name="Test Viewer",
                    email=f"viewer-{uuid.uuid4().hex[:8]}@example.com",
                    password_hash="test-password-hash",
                    role="viewer",
                    is_active=True,
                ),
                User(
                    id=foreign_user_id,
                    organization_id=foreign_organization_id,
                    full_name="Foreign Admin",
                    email=f"foreign-admin-{uuid.uuid4().hex[:8]}@example.com",
                    password_hash="test-password-hash",
                    role="admin",
                    is_active=True,
                ),
            ])

            session.add_all([
                Employee(
                    id=employee_id,
                    organization_id=organization_id,
                    employee_code="TEST-EMP-001",
                    full_name="Test Employee",
                    email=f"employee-{uuid.uuid4().hex[:8]}@example.com",
                    department="Engineering",
                    job_title="Developer",
                ),
                Employee(
                    id=foreign_employee_id,
                    organization_id=foreign_organization_id,
                    employee_code="FOREIGN-EMP-001",
                    full_name="Foreign Employee",
                    email=f"foreign-{uuid.uuid4().hex[:8]}@example.com",
                    department="Finance",
                    job_title="Analyst",
                ),
            ])

            await session.flush()

            session.add_all([
                Alert(
                    id=open_alert_id,
                    organization_id=organization_id,
                    employee_id=employee_id,
                    risk_score=85.0,
                    severity="high",
                    status="open",
                    title="Unusual Data Access",
                    description="Test alert with open status",
                    detection_count=1,
                    contributing_factors={"test": True},
                ),
                Alert(
                    id=acknowledged_alert_id,
                    organization_id=organization_id,
                    employee_id=employee_id,
                    risk_score=70.0,
                    severity="medium",
                    status="acknowledged",
                    title="Suspicious Login",
                    description="Test alert with acknowledged status",
                    detection_count=2,
                    contributing_factors={"test": True},
                ),
                Alert(
                    id=resolved_alert_id,
                    organization_id=organization_id,
                    employee_id=employee_id,
                    risk_score=95.0,
                    severity="critical",
                    status="resolved",
                    title="Resolved Security Incident",
                    description="Test alert with resolved status",
                    detection_count=3,
                    contributing_factors={"test": True},
                ),
                Alert(
                    id=foreign_alert_id,
                    organization_id=foreign_organization_id,
                    employee_id=foreign_employee_id,
                    risk_score=90.0,
                    severity="high",
                    status="open",
                    title="Foreign Organization Alert",
                    description="Must not be visible to the test organization",
                    detection_count=1,
                    contributing_factors={"test": True},
                ),
            ])

            await session.flush()

            session.add_all([
                Investigation(
                    id=open_investigation_id,
                    organization_id=organization_id,
                    employee_id=employee_id,
                    title="Open Test Investigation",
                    description="Investigation used for authorization tests",
                    status="open",
                    priority="high",
                    assigned_to=analyst_id,
                    created_by=admin_id,
                ),
                Investigation(
                    id=closed_investigation_id,
                    organization_id=organization_id,
                    employee_id=employee_id,
                    title="Closed Test Investigation",
                    description="Investigation used for closed-state tests",
                    status="closed",
                    priority="medium",
                    assigned_to=analyst_id,
                    created_by=admin_id,
                ),
                Investigation(
                    id=foreign_investigation_id,
                    organization_id=foreign_organization_id,
                    employee_id=foreign_employee_id,
                    title="Foreign Test Investigation",
                    description="Must not be visible to the test organization",
                    status="open",
                    priority="high",
                    assigned_to=None,
                    created_by=foreign_user_id,
                ),
            ])

            await session.commit()

        tokens = {
            "admin": create_access_token(
                user_id=admin_id,
                organization_id=organization_id,
                role="admin",
            ),
            "analyst": create_access_token(
                user_id=analyst_id,
                organization_id=organization_id,
                role="analyst",
            ),
            "viewer": create_access_token(
                user_id=viewer_id,
                organization_id=organization_id,
                role="viewer",
            ),
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield {
                "client": client,
                "tokens": tokens,
                "employee_id": employee_id,
                "foreign_employee_id": foreign_employee_id,
                "open_alert_id": open_alert_id,
                "acknowledged_alert_id": acknowledged_alert_id,
                "resolved_alert_id": resolved_alert_id,
                "foreign_alert_id": foreign_alert_id,
                "open_investigation_id": open_investigation_id,
                "closed_investigation_id": closed_investigation_id,
                "foreign_investigation_id": foreign_investigation_id,
                "api_prefix": settings.api_v1_prefix,
            }

    finally:
        try:
            async with session_factory() as session:
                await session.execute(
                    delete(Organization).where(
                        Organization.id.in_([
                            organization_id,
                            foreign_organization_id,
                        ])
                    )
                )
                await session.commit()
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            await engine.dispose()
