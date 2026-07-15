"""HTTP API integration tests for MVP 2 training endpoints."""

from datetime import UTC, date, datetime, timedelta
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
def test_http_training_plan_and_report_flow(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_date = (datetime.now(UTC).date() + timedelta(days=7)).isoformat()
    create_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/day",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "start_date": start_date,
            "workouts": [_workout_payload(start_date)],
        },
    )
    assert create_response.status_code == 201
    workout_id = create_response.json()["workouts"][0]["id"]

    plan_response = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/training-plan",
        headers={"Authorization": f"Bearer {coach_token}"},
        params={"period": "week", "anchor_date": start_date},
    )
    assert plan_response.status_code == 200
    assert len(plan_response.json()["workouts"]) == 1
    assert plan_response.json()["workouts"][0]["cycles"][0]["exercises"][0]["name"] == "Jog"

    athlete_plan_response = client.get(
        "/api/v1/athlete/training-plan",
        headers={"Authorization": f"Bearer {athlete_token}"},
        params={"period": "month", "anchor_date": start_date},
    )
    assert athlete_plan_response.status_code == 200
    assert len(athlete_plan_response.json()["workouts"]) == 1

    athlete_text_response = client.get(
        "/api/v1/athlete/training-plan/text",
        headers={"Authorization": f"Bearer {athlete_token}"},
        params={"period": "week", "anchor_date": start_date},
    )
    assert athlete_text_response.status_code == 200
    assert "text" in athlete_text_response.json()

    report_response = client.post(
        f"/api/v1/athlete/planned-workouts/{workout_id}/report",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={"difficulty_rating": 7, "mood_rating": 8, "comment": "Solid"},
    )
    assert report_response.status_code == 201

    reports_response = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/workout-reports",
        headers={"Authorization": f"Bearer {coach_token}"},
        params={"period": "week"},
    )
    assert reports_response.status_code == 200
    assert len(reports_response.json()["reports"]) == 1
    assert reports_response.json()["reports"][0]["difficulty_rating"] == 7

    coach_text_response = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/training-plan/text",
        headers={"Authorization": f"Bearer {coach_token}"},
        params={"period": "week", "anchor_date": start_date},
    )
    assert coach_text_response.status_code == 200
    assert "text" in coach_text_response.json()


@pytest.mark.integration
def test_http_training_text_endpoints_not_implemented(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_date = (datetime.now(UTC).date() + timedelta(days=7)).isoformat()
    parse_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/parse",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"scope": "week", "start_date": start_date, "text": "8 Июня\n\nСуставная разминка"},
    )
    assert parse_response.status_code == 200
    assert parse_response.json()["detected_scope"] == "week"

    from_text_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/from-text",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"scope": "week", "start_date": start_date, "text": "8 Июня\n\nСуставная разминка"},
    )
    assert from_text_response.status_code == 201
    assert from_text_response.json()["scope"] == "week"


@pytest.mark.integration
def test_http_update_training_plan_raw_text_preserves_past_reports(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    today = datetime.now(UTC).date()
    start_date = (today - timedelta(days=3)).isoformat()
    create_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/week",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "start_date": start_date,
            "workouts": [
                _workout_payload((today - timedelta(days=3)).isoformat()),
                _workout_payload((today - timedelta(days=2)).isoformat()),
                _workout_payload((today - timedelta(days=1)).isoformat()),
                _workout_payload((today + timedelta(days=1)).isoformat()),
                _workout_payload((today + timedelta(days=2)).isoformat()),
            ],
        },
    )
    assert create_response.status_code == 201
    plan_id = create_response.json()["id"]
    past_workout_id = create_response.json()["workouts"][1]["id"]

    report_response = client.post(
        f"/api/v1/athlete/planned-workouts/{past_workout_id}/report",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={
            "difficulty_rating": 7,
            "mood_rating": 8,
            "comment": "Solid",
            "raw_report_text": "нагрузка 6-7",
        },
    )
    assert report_response.status_code == 201

    raw_text = "\t".join(
        [
            "8 Июня\n\nСуставная разминка",
            "9 Июня\n\nВелостанок\n\n60 мин",
            "10 Июня\n\nСуставная разминка",
            "11 Июня\n\nСуставная разминка",
            "12 Июня\n\nСуставная разминка",
            "13 Июня\n\nСуставная разминка",
            "14 Июня\n\nСуставная разминка",
        ]
    )
    patch_response = client.patch(
        f"/api/v1/coach/training-plans/{plan_id}/raw-text",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"raw_text": raw_text},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["plan"]["raw_text"] is not None
    assert patch_response.json()["replaced_workouts_count"] >= 1

    reports_response = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/workout-reports",
        headers={"Authorization": f"Bearer {coach_token}"},
        params={"period": "week"},
    )
    assert reports_response.status_code == 200
    assert len(reports_response.json()["reports"]) == 1


@pytest.mark.integration
def test_http_coach_cannot_view_unlinked_athlete_training_plan(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    _, athlete_token = _register_and_login(client, "athlete")
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    response = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/training-plan",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"


def _build_week_text(start: date) -> str:
    months = {
        1: "Января",
        2: "Февраля",
        3: "Марта",
        4: "Апреля",
        5: "Мая",
        6: "Июня",
        7: "Июля",
        8: "Августа",
        9: "Сентября",
        10: "Октября",
        11: "Ноября",
        12: "Декабря",
    }
    blocks = []
    for offset in range(7):
        day = start + timedelta(days=offset)
        month = months[day.month]
        blocks.append(f"{day.day} {month}\n\nБег {offset + 1} км")
    return "\n\n".join(blocks)


@pytest.mark.integration
def test_http_create_week_from_text_creates_seven_workouts(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_date = datetime.now(UTC).date() + timedelta(days=7)
    week_text = _build_week_text(start_date)

    create_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/from-text",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "scope": "week",
            "start_date": start_date.isoformat(),
            "text": week_text,
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["scope"] == "week"
    assert len(create_response.json()["workouts"]) == 7

    plan_response = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/training-plan",
        headers={"Authorization": f"Bearer {coach_token}"},
        params={"period": "week", "anchor_date": start_date.isoformat()},
    )
    assert plan_response.status_code == 200
    assert len(plan_response.json()["workouts"]) == 7


@pytest.mark.integration
def test_http_patch_day_plan_with_week_scope_creates_multiple_workouts(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    _, coach_token = _register_and_login(client, "coach")
    athlete_email, athlete_token = _register_and_login(client, "athlete")
    _link_coach_and_athlete(client, coach_token, athlete_email, athlete_token)
    athlete_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    ).json()["id"]

    start_date = datetime.now(UTC).date() + timedelta(days=14)
    day_response = client.post(
        f"/api/v1/coach/athletes/{athlete_id}/training-plans/from-text",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "scope": "day",
            "start_date": start_date.isoformat(),
            "text": "Разминка\n\n20 мин бега",
        },
    )
    assert day_response.status_code == 201
    plan_id = day_response.json()["id"]
    assert day_response.json()["scope"] == "day"
    assert len(day_response.json()["workouts"]) == 1

    week_text = _build_week_text(start_date)
    patch_response = client.patch(
        f"/api/v1/coach/training-plans/{plan_id}/raw-text",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "raw_text": week_text,
            "scope": "week",
            "start_date": start_date.isoformat(),
        },
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["plan"]["scope"] == "week"
    assert patch_response.json()["replaced_workouts_count"] == 7

    plan_response = client.get(
        f"/api/v1/coach/athletes/{athlete_id}/training-plan",
        headers={"Authorization": f"Bearer {coach_token}"},
        params={"period": "week", "anchor_date": start_date.isoformat()},
    )
    assert plan_response.status_code == 200
    assert len(plan_response.json()["workouts"]) == 7
