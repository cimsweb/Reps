"""HTTP integration tests for coaching API."""

from datetime import UTC, datetime
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
def test_coaching_read_flow(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    coach_email, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    coach_headers = {"Authorization": f"Bearer {coach_token}"}
    athlete_headers = {"Authorization": f"Bearer {athlete_token}"}

    invite_response = client.post(
        "/api/v1/coach/invitations",
        headers=coach_headers,
        json={"email": athlete_email},
    )
    assert invite_response.status_code == 201
    invitation_id = invite_response.json()["id"]

    pending_response = client.get("/api/v1/athlete/invitations", headers=athlete_headers)
    assert pending_response.status_code == 200
    assert len(pending_response.json()["items"]) == 1

    accept_response = client.post(
        f"/api/v1/athlete/invitations/{invitation_id}/accept",
        headers=athlete_headers,
    )
    assert accept_response.status_code == 200
    athlete_id = accept_response.json()["athlete_id"]

    coach_invitations = client.get("/api/v1/coach/invitations", headers=coach_headers)
    assert coach_invitations.status_code == 200
    assert coach_invitations.json()["items"][0]["status"] == "accepted"

    coach_athletes = client.get("/api/v1/coach/athletes", headers=coach_headers)
    assert coach_athletes.status_code == 200
    assert len(coach_athletes.json()["items"]) == 1

    athlete_coaches = client.get("/api/v1/athlete/coaches", headers=athlete_headers)
    assert athlete_coaches.status_code == 200
    assert len(athlete_coaches.json()["items"]) == 1

    profile_response = client.put(
        "/api/v1/athlete/profile",
        headers=athlete_headers,
        json={"height_cm": 180, "weight_kg": 75, "age": 28, "gender": "male"},
    )
    assert profile_response.status_code == 200

    own_profile = client.get("/api/v1/athlete/profile", headers=athlete_headers)
    assert own_profile.status_code == 200
    assert own_profile.json()["height_cm"] == 180

    coach_profile = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/profile",
        headers=coach_headers,
    )
    assert coach_profile.status_code == 200
    assert coach_profile.json()["age"] == 28

    record_response = client.post(
        "/api/v1/athlete/records",
        headers=athlete_headers,
        json={
            "record_type": "distance",
            "name": "5K",
            "value": "19:45",
            "unit": "time",
            "achieved_at": datetime.now(UTC).isoformat(),
        },
    )
    assert record_response.status_code == 201

    own_records = client.get("/api/v1/athlete/records", headers=athlete_headers)
    assert own_records.status_code == 200
    assert own_records.json()["total"] == 1

    coach_records = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/records",
        headers=coach_headers,
    )
    assert coach_records.status_code == 200
    assert coach_records.json()["total"] == 1

    feedback_response = client.post(
        "/api/v1/athlete/feedback",
        headers=athlete_headers,
        json={"text": "Legs felt heavy."},
    )
    assert feedback_response.status_code == 201
    assert feedback_response.json()["text"] == "Legs felt heavy."

    coach_feedback = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/feedback",
        headers=coach_headers,
    )
    assert coach_feedback.status_code == 200
    assert coach_feedback.json()["total"] == 1

    _ = coach_email


@pytest.mark.integration
def test_coach_cannot_access_unlinked_athlete_profile(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    _, athlete_token = _register_and_login(client, "athlete")
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    response = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/profile",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"


@pytest.mark.integration
def test_feedback_pagination_returns_total(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, athlete_token = _register_and_login(client, "athlete")
    athlete_headers = {"Authorization": f"Bearer {athlete_token}"}

    for index in range(3):
        response = client.post(
            "/api/v1/athlete/feedback",
            headers=athlete_headers,
            json={"text": f"Session {index}"},
        )
        assert response.status_code == 201

    page_response = client.get(
        "/api/v1/athlete/feedback?offset=0&limit=2",
        headers=athlete_headers,
    )
    assert page_response.status_code == 200
    body = page_response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
