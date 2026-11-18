import pytest


@pytest.mark.asyncio
async def test_analyst_can_create_employee(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["analyst"]
    prefix = api_context["api_prefix"]

    response = await client.post(
        f"{prefix}/employees",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "employee_code": "NEW-EMP-001",
            "full_name": "New Test Employee",
            "email": "new.employee@example.com",
            "department": "Engineering",
            "job_title": "Backend Developer",
        },
    )

    assert response.status_code == 201
    assert response.json()["employee_code"] == "NEW-EMP-001"


@pytest.mark.asyncio
async def test_admin_can_update_employee(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["admin"]
    prefix = api_context["api_prefix"]
    employee_id = api_context["employee_id"]

    response = await client.patch(
        f"{prefix}/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"department": "Security"},
    )

    assert response.status_code == 200
    assert response.json()["department"] == "Security"


@pytest.mark.asyncio
async def test_viewer_can_read_but_cannot_write_employees(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["viewer"]
    prefix = api_context["api_prefix"]
    employee_id = api_context["employee_id"]

    headers = {"Authorization": f"Bearer {token}"}

    read_response = await client.get(
        f"{prefix}/employees/{employee_id}",
        headers=headers,
    )

    assert read_response.status_code == 200

    create_response = await client.post(
        f"{prefix}/employees",
        headers=headers,
        json={
            "employee_code": "VIEWER-EMP-001",
            "full_name": "Viewer Created Employee",
            "email": "viewer.created@example.com",
        },
    )

    assert create_response.status_code == 403

    update_response = await client.patch(
        f"{prefix}/employees/{employee_id}",
        headers=headers,
        json={"department": "Unauthorized"},
    )

    assert update_response.status_code == 403


@pytest.mark.asyncio
async def test_organization_cannot_access_foreign_employee(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["admin"]
    prefix = api_context["api_prefix"]
    foreign_employee_id = api_context["foreign_employee_id"]

    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        f"{prefix}/employees/{foreign_employee_id}",
        headers=headers,
    )

    assert response.status_code == 404

    list_response = await client.get(
        f"{prefix}/employees",
        headers=headers,
    )

    assert list_response.status_code == 200

    returned_ids = {
        employee["id"]
        for employee in list_response.json()
    }

    assert str(foreign_employee_id) not in returned_ids
