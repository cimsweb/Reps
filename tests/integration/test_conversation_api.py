"""HTTP integration tests for conversations API."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from integration.conftest import database_is_available
from interfaces.http.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _register_and_login(client: TestClient, role: str) -> tuple[str, str]:
    email = f"{role}-{uuid4()}@example.com"
    password = "secure1A"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_response.json()["token"]
    return email, token


@pytest.mark.integration
def test_conversation_messaging_flow(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    coach_headers = {"Authorization": f"Bearer {coach_token}"}
    athlete_headers = {"Authorization": f"Bearer {athlete_token}"}

    invite_response = client.post(
        "/api/v1/coach/invitations",
        headers=coach_headers,
        json={"email": athlete_email},
    )
    invitation_id = invite_response.json()["id"]
    accept_response = client.post(
        f"/api/v1/athlete/invitations/{invitation_id}/accept",
        headers=athlete_headers,
    )
    athlete_id = accept_response.json()["athlete_id"]
    coaches_response = client.get("/api/v1/athlete/coaches", headers=athlete_headers)
    coach_id = coaches_response.json()["items"][0]["coach_id"]

    send_coach_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/messages",
        headers=coach_headers,
        json={"content": "Как самочувствие?", "kind": "text"},
    )
    assert send_coach_response.status_code == 201
    assert send_coach_response.json()["content"] == "Как самочувствие?"
    assert send_coach_response.json()["is_mine"] is True

    coach_list_response = client.get("/api/v1/coach/conversations", headers=coach_headers)
    assert coach_list_response.status_code == 200
    assert len(coach_list_response.json()["items"]) == 1
    conversation_id = coach_list_response.json()["items"][0]["id"]

    send_athlete_response = client.post(
        f"/api/v1/athlete/coaches/{coach_id}/messages",
        headers=athlete_headers,
        json={"content": "Нормально, но устал", "kind": "question"},
    )
    assert send_athlete_response.status_code == 201
    assert send_athlete_response.json()["kind"] == "question"

    messages_response = client.get(
        f"/api/v1/athlete/conversations/{conversation_id}/messages",
        headers=athlete_headers,
    )
    assert messages_response.status_code == 200
    assert messages_response.json()["total"] == 2
    assert len(messages_response.json()["items"]) == 2

    read_response = client.post(
        f"/api/v1/coach/conversations/{conversation_id}/read",
        headers=coach_headers,
    )
    assert read_response.status_code == 200
    assert read_response.json()["marked_count"] == 1

    coach_list_after_read = client.get("/api/v1/coach/conversations", headers=coach_headers)
    assert coach_list_after_read.json()["items"][0]["unread_count"] == 0
