
import pytest


@pytest.mark.asyncio
async def test_viewer_can_read_but_cannot_create_investigation(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["viewer"]
    prefix = api_context["api_prefix"]
    investigation_id = api_context["open_investigation_id"]

    headers = {"Authorization": f"Bearer {token}"}

    read_response = await client.get(
        f"{prefix}/investigations/{investigation_id}",
        headers=headers,
    )

    assert read_response.status_code == 200

    create_response = await client.post(
        f"{prefix}/investigations",
        headers=headers,
        json={
            "title": "Viewer Created Investigation",
            "description": "This request must be rejected",
            "priority": "medium",
        },
    )

    assert create_response.status_code == 403


@pytest.mark.asyncio
async def test_analyst_can_create_investigation(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["analyst"]
    prefix = api_context["api_prefix"]

    response = await client.post(
        f"{prefix}/investigations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Analyst Created Investigation",
            "description": "Created during authorization testing",
            "employee_id": str(api_context["employee_id"]),
            "assigned_to": str(
                # The analyst is an authorized assignee in this organization.
                # Its ID is represented by the fixture's analyst token subject.
                api_context["tokens"]["analyst"]
            ) if False else None,
            "priority": "high",
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Analyst Created Investigation"
    assert response.json()["status"] == "open"
    assert response.json()["organization_id"]


@pytest.mark.asyncio
async def test_viewer_cannot_update_investigation(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["viewer"]
    prefix = api_context["api_prefix"]
    investigation_id = api_context["open_investigation_id"]

    response = await client.patch(
        f"{prefix}/investigations/{investigation_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Unauthorized Investigation Update"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_foreign_organization_cannot_access_investigation(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["admin"]
    prefix = api_context["api_prefix"]
    foreign_id = api_context["foreign_investigation_id"]

    headers = {"Authorization": f"Bearer {token}"}

    detail_response = await client.get(
        f"{prefix}/investigations/{foreign_id}",
        headers=headers,
    )

    assert detail_response.status_code == 404

    list_response = await client.get(
        f"{prefix}/investigations",
        headers=headers,
    )

    assert list_response.status_code == 200

    returned_ids = {
        item["id"]
        for item in list_response.json()
    }

    assert str(foreign_id) not in returned_ids


@pytest.mark.asyncio
async def test_investigation_can_be_closed_but_not_modified_afterward(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["analyst"]
    prefix = api_context["api_prefix"]
    investigation_id = api_context["open_investigation_id"]

    headers = {"Authorization": f"Bearer {token}"}

    close_response = await client.patch(
        f"{prefix}/investigations/{investigation_id}",
        headers=headers,
        json={"status": "closed"},
    )

    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"
    assert close_response.json()["closed_at"] is not None

    modify_response = await client.patch(
        f"{prefix}/investigations/{investigation_id}",
        headers=headers,
        json={"title": "Attempt to Modify Closed Investigation"},
    )

    assert modify_response.status_code == 409
    assert modify_response.json()["detail"] == (
        "Closed investigations cannot be modified"
    )
