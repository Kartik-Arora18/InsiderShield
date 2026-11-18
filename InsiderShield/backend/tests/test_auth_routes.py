
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.main import app

client = TestClient(app)


def test_me_requires_bearer_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_admin_check_requires_bearer_token():
    response = client.get("/api/v1/auth/admin-check")
    assert response.status_code == 401


def _check_admin_access(role: str):
    fake_user = SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        role=role,
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user

    try:
        return client.get("/api/v1/auth/admin-check")
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_admin_can_access_admin_check():
    response = _check_admin_access("admin")

    assert response.status_code == 200
    assert response.json()["message"] == "Admin access granted"


def test_analyst_cannot_access_admin_check():
    response = _check_admin_access("analyst")

    assert response.status_code == 403


def test_viewer_cannot_access_admin_check():
    response = _check_admin_access("viewer")

    assert response.status_code == 403
