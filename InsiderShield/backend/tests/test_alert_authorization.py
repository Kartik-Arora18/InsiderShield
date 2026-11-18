
import pytest


@pytest.mark.asyncio
async def test_viewer_can_read_but_cannot_update_alert(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["viewer"]
    prefix = api_context["api_prefix"]
    alert_id = api_context["open_alert_id"]

    headers = {"Authorization": f"Bearer {token}"}

    read_response = await client.get(
        f"{prefix}/alerts/{alert_id}",
        headers=headers,
    )

    assert read_response.status_code == 200
    assert read_response.json()["status"] == "open"

    update_response = await client.patch(
        f"{prefix}/alerts/{alert_id}/status",
        headers=headers,
        json={"status": "acknowledged"},
    )

    assert update_response.status_code == 403


@pytest.mark.asyncio
async def test_analyst_can_acknowledge_open_alert(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["analyst"]
    prefix = api_context["api_prefix"]
    alert_id = api_context["open_alert_id"]

    response = await client.patch(
        f"{prefix}/alerts/{alert_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "acknowledged"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"


@pytest.mark.asyncio
async def test_open_alert_cannot_be_resolved_directly(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["analyst"]
    prefix = api_context["api_prefix"]
    alert_id = api_context["open_alert_id"]

    response = await client.patch(
        f"{prefix}/alerts/{alert_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "resolved"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "An open alert must be acknowledged before resolution"
    )


@pytest.mark.asyncio
async def test_resolved_alert_cannot_be_modified(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["admin"]
    prefix = api_context["api_prefix"]
    alert_id = api_context["resolved_alert_id"]

    response = await client.patch(
        f"{prefix}/alerts/{alert_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "acknowledged"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A resolved alert cannot be modified"
    )


@pytest.mark.asyncio
async def test_organization_cannot_access_foreign_alert(api_context):
    client = api_context["client"]
    token = api_context["tokens"]["admin"]
    prefix = api_context["api_prefix"]
    foreign_alert_id = api_context["foreign_alert_id"]

    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        f"{prefix}/alerts/{foreign_alert_id}",
        headers=headers,
    )

    assert response.status_code == 404

    list_response = await client.get(
        f"{prefix}/alerts",
        headers=headers,
    )

    assert list_response.status_code == 200

    returned_ids = {
        alert["id"]
        for alert in list_response.json()
    }

    assert str(foreign_alert_id) not in returned_ids
