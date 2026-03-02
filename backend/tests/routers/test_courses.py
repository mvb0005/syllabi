"""Tests for the /courses router."""

import uuid

import pytest
from httpx import AsyncClient


async def _make_and_login_instructor(client: AsyncClient) -> str:
    """Create an instructor user, log in, and return their id.

    After this call the client's cookie jar contains the access_token,
    so subsequent requests will be authenticated as this instructor.
    """
    email = f"instructor-{uuid.uuid4()}@courses-test.com"
    create_resp = await client.post(
        "/users/",
        json={
            "email": email,
            "full_name": "Instructor",
            "role": "instructor",
            "password": "pass",
        },
    )
    assert create_resp.status_code == 201
    user_id = str(create_resp.json()["id"])

    login_resp = await client.post("/auth/login", json={"email": email, "password": "pass"})
    assert login_resp.status_code == 200
    return user_id


@pytest.mark.asyncio
async def test_create_course(client: AsyncClient) -> None:
    """POST /courses/ creates a course and returns 201."""
    instructor_id = await _make_and_login_instructor(client)
    response = await client.post(
        "/courses/",
        json={"title": "Intro to Python", "description": "Learn Python basics"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Intro to Python"
    assert data["instructor_id"] == instructor_id
    assert data["is_published"] is False


@pytest.mark.asyncio
async def test_get_course_not_found(client: AsyncClient) -> None:
    """GET /courses/{id} returns 404 for unknown ID."""
    response = await client.get("/courses/does-not-exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_course(client: AsyncClient) -> None:
    """PATCH /courses/{id} updates the course."""
    await _make_and_login_instructor(client)
    create_resp = await client.post("/courses/", json={"title": "Old Title"})
    assert create_resp.status_code == 201
    course_id = create_resp.json()["id"]
    response = await client.patch(
        f"/courses/{course_id}", json={"title": "New Title", "is_published": True}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["is_published"] is True
