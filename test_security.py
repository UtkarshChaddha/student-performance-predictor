import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_is_alive(client):
    response = client.get("/")
    assert response.status_code == 200


def test_students_requires_authentication(client):
    response = client.get("/api/students")
    assert response.status_code in (401, 403)


def test_public_student_creation_is_blocked(client):
    response = client.post(
        "/api/students",
        json={
            "name": "Hacker",
            "email": "hacker@example.com",
            "age": 20,
            "course": "BCA",
            "interest_level": 5,
            "learning_depth": 5,
        },
    )

    assert response.status_code in (401, 403, 404, 405)


def test_legacy_student_creation_is_admin_only(client):
    response = client.post(
        "/students",
        json={
            "name": "Hacker",
            "email": "hacker@example.com",
            "age": 20,
            "course": "BCA",
            "interest_level": 5,
            "learning_depth": 5,
        },
    )

    assert response.status_code in (401, 403)


def test_login_rejects_extra_fields(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123!",
            "role": "admin",
            "is_admin": True,
        },
    )

    assert response.status_code == 422


def test_register_rejects_extra_fields(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "role": "admin",
            "is_admin": True,
        },
    )

    assert response.status_code == 422


def test_progress_requires_authentication(client):
    response = client.get("/api/progress/1")
    assert response.status_code in (401, 403)


def test_subject_creation_requires_authentication(client):
    response = client.post(
        "/api/subjects",
        json={"name": "Hacking 101"},
    )

    assert response.status_code in (401, 403)


def test_logout_requires_authentication(client):
    response = client.post("/auth/logout")
    assert response.status_code in (401, 403)