"""HTTP API integration tests for MVP 2.2 training AI endpoints."""

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


def _link_coach_and_athlete(
    client: TestClient,
    coach_token: str,
    athlete_email: str,
    athlete_token: str,
) -> None:
    invitation_response = client.post(
        "/api/v1/coach/invitations",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"email": athlete_email},
    )
    invitation_id = invitation_response.json()["id"]
    client.post(
        f"/api/v1/athlete/invitations/{invitation_id}/accept",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )


def _workout_payload(planned_date: str) -> dict[str, object]:
    return {
        "planned_date": planned_date,
        "workout_type": "run",
        "title": "Morning run",
        "cycles": [
            {
                "name": "Main",
                "sort_order": 0,
                "exercises": [
                    {
                        "name": "Jog",
                        "details": "5 km",
                        "sort_order": 0,
                    }
                ],
            }
        ],
    }


@pytest.mark.integration
def test_http_plan_agent_dialog_confirm_creates_plan(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_date = "2024-06-08"
    start_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/ai/sessions",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"start_date": start_date, "initial_brief": "бег зал бег отдых бег вело бег"},
    )
    assert start_response.status_code == 201
    session_id = start_response.json()["session_id"]
    assert start_response.json()["latest_reply"]["type"] == "question"

    message_response = client.post(
        f"/api/v1/coach/training-plans/ai/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"content": "120 минут"},
    )
    assert message_response.status_code == 200
    assert message_response.json()["latest_reply"]["type"] == "plan_draft"
    assert message_response.json()["can_confirm"] is True

    confirm_response = client.post(
        f"/api/v1/coach/training-plans/ai/sessions/{session_id}/confirm",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={},
    )
    assert confirm_response.status_code == 201
    assert confirm_response.json()["scope"] == "week"
    assert len(confirm_response.json()["workouts"]) >= 1


@pytest.mark.integration
def test_http_report_agent_dialog_confirm_creates_report(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_date = datetime.now(UTC).date().isoformat()
    create_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/day",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"start_date": start_date, "workouts": [_workout_payload(start_date)]},
    )
    assert create_response.status_code == 201
    workout_id = create_response.json()["workouts"][0]["id"]

    start_session = client.post(
        f"/api/v1/athlete/planned-workouts/{workout_id}/report/ai/sessions",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    assert start_session.status_code == 201
    session_id = start_session.json()["session_id"]

    first_message = client.post(
        f"/api/v1/athlete/report/ai/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={"content": "нагрузка 5"},
    )
    assert first_message.status_code == 200
    assert first_message.json()["latest_reply"]["type"] == "question"

    second_message = client.post(
        f"/api/v1/athlete/report/ai/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={"content": "тяжело на интервалах"},
    )
    assert second_message.status_code == 200
    assert second_message.json()["latest_reply"]["type"] == "question"

    third_message = client.post(
        f"/api/v1/athlete/report/ai/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={"content": "настроение нормальное"},
    )
    assert third_message.status_code == 200
    assert third_message.json()["latest_reply"]["type"] == "report_draft"
    assert third_message.json()["can_confirm"] is True

    confirm_response = client.post(
        f"/api/v1/athlete/report/ai/sessions/{session_id}/confirm",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={},
    )
    assert confirm_response.status_code == 201
    assert confirm_response.json()["difficulty_rating"] == 5
    assert confirm_response.json()["mood_rating"] == 7


@pytest.mark.integration
def test_http_plan_agent_message_limit_returns_429(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/ai/sessions",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"start_date": "2024-06-08"},
    )
    assert start_response.status_code == 201
    session_id = start_response.json()["session_id"]

    for index in range(10):
        response = client.post(
            f"/api/v1/coach/training-plans/ai/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {coach_token}"},
            json={"content": f"message {index}"},
        )
        assert response.status_code == 200

    limit_response = client.post(
        f"/api/v1/coach/training-plans/ai/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"content": "one too many"},
    )
    assert limit_response.status_code == 429
    assert limit_response.json()["error"] == "message_limit"


@pytest.mark.integration
def test_http_get_plan_agent_session_returns_ordered_messages(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/ai/sessions",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"start_date": "2024-06-08", "initial_brief": "бег зал бег"},
    )
    assert start_response.status_code == 201
    session_id = start_response.json()["session_id"]

    client.post(
        f"/api/v1/coach/training-plans/ai/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"content": "120 минут"},
    )

    get_response = client.get(
        f"/api/v1/coach/training-plans/ai/sessions/{session_id}",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["session_id"] == session_id
    assert len(body["messages"]) == 4
    sort_orders = [message["sort_order"] for message in body["messages"]]
    assert sort_orders == sorted(sort_orders)
    assert body["latest_reply"]["type"] == "plan_draft"
    assert body["can_confirm"] is True


@pytest.mark.integration
def test_http_get_active_plan_agent_session_for_athlete(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/ai/sessions",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"start_date": "2024-06-08"},
    )
    assert start_response.status_code == 201
    session_id = start_response.json()["session_id"]

    active_response = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/ai/sessions/active",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert active_response.status_code == 200
    assert active_response.json()["session_id"] == session_id
    assert active_response.json()["status"] == "active"


@pytest.mark.integration
def test_http_get_active_report_agent_session_for_workout(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_date = datetime.now(UTC).date().isoformat()
    create_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/day",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"start_date": start_date, "workouts": [_workout_payload(start_date)]},
    )
    workout_id = create_response.json()["workouts"][0]["id"]

    start_session = client.post(
        f"/api/v1/athlete/planned-workouts/{workout_id}/report/ai/sessions",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    assert start_session.status_code == 201
    session_id = start_session.json()["session_id"]

    active_response = client.get(
        f"/api/v1/athlete/planned-workouts/{workout_id}/report/ai/sessions/active",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    assert active_response.status_code == 200
    assert active_response.json()["session_id"] == session_id


@pytest.mark.integration
def test_http_plan_agent_session_forbidden_for_other_coach(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    _, other_coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/ai/sessions",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"start_date": "2024-06-08"},
    )
    session_id = start_response.json()["session_id"]

    forbidden_response = client.get(
        f"/api/v1/coach/training-plans/ai/sessions/{session_id}",
        headers={"Authorization": f"Bearer {other_coach_token}"},
    )
    assert forbidden_response.status_code == 403


@pytest.mark.integration
def test_http_report_agent_session_forbidden_for_other_athlete(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _, other_athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_date = datetime.now(UTC).date().isoformat()
    create_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/day",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"start_date": start_date, "workouts": [_workout_payload(start_date)]},
    )
    workout_id = create_response.json()["workouts"][0]["id"]

    start_session = client.post(
        f"/api/v1/athlete/planned-workouts/{workout_id}/report/ai/sessions",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    session_id = start_session.json()["session_id"]

    forbidden_response = client.get(
        f"/api/v1/athlete/report/ai/sessions/{session_id}",
        headers={"Authorization": f"Bearer {other_athlete_token}"},
    )
    assert forbidden_response.status_code == 403
