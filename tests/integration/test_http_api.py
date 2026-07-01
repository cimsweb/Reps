"""HTTP API integration tests."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from integration.conftest import database_is_available
from interfaces.http.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.mark.integration
def test_http_register_login_and_me_flow(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    email = f"ui-{uuid4()}@example.com"
    password = "secure1A"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": "coach"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["role"] == "coach"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


@pytest.mark.integration
def test_http_coach_cannot_access_admin_users(client: TestClient) -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    email = f"ui-{uuid4()}@example.com"
    password = "secure1A"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": "coach"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_response.json()["token"]

    users_response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert users_response.status_code == 403
    assert users_response.json()["error"] == "forbidden"
