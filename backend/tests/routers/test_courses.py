"""Tests for the /courses router."""

import uuid

import pytest
from httpx import AsyncClient


async def _make_instructor(client: AsyncClient) -> str:
    """Helper: create an instructor user and return their id."""
    resp = await client.post(
        "/users/",
        json={
            "email": f"instructor-{uuid.uuid4()}@courses-test.com",
            "full_name": "Instructor",
            "role": "instructor",
            "password": "pass",
        },
    )
    return str(resp.json()["id"])


@pytest.mark.asyncio
async def test_create_course(client: AsyncClient) -> None:
    """POST /courses/ creates a course and returns 201."""
    instructor_id = await _make_instructor(client)
    response = await client.post(
        "/courses/",
        json={
            "title": "Intro to Python",
            "description": "Learn Python basics",
            "instructor_id": instructor_id,
        },
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
    instructor_id = await _make_instructor(client)
    create_resp = await client.post(
        "/courses/",
        json={"title": "Old Title", "instructor_id": instructor_id},
    )
    course_id = create_resp.json()["id"]
    response = await client.patch(
        f"/courses/{course_id}", json={"title": "New Title", "is_published": True}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["is_published"] is True
