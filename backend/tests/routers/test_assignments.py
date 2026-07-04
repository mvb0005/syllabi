"""Tests for the /assignments router."""

import uuid

import pytest
from httpx import AsyncClient


async def _make_module(client: AsyncClient) -> str:
    """Create an instructor, course, and module; return the module id."""
    email = f"instructor-{uuid.uuid4()}@assignments-test.com"
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
    login_resp = await client.post("/auth/login", json={"email": email, "password": "pass"})
    assert login_resp.status_code == 200

    course_resp = await client.post("/courses/", json={"title": "Course"})
    assert course_resp.status_code == 201
    module_resp = await client.post(
        f"/courses/{course_resp.json()['id']}/modules", json={"title": "Module"}
    )
    assert module_resp.status_code == 201
    return str(module_resp.json()["id"])


@pytest.mark.asyncio
async def test_list_assignments(client: AsyncClient) -> None:
    """GET /assignments/?module_id= returns the module's assignments in creation order."""
    module_id = await _make_module(client)
    for title in ["Exercise 1", "Exercise 2"]:
        create_resp = await client.post(
            f"/assignments/?module_id={module_id}", json={"title": title}
        )
        assert create_resp.status_code == 201

    response = await client.get(f"/assignments/?module_id={module_id}")
    assert response.status_code == 200
    assert [a["title"] for a in response.json()] == ["Exercise 1", "Exercise 2"]


@pytest.mark.asyncio
async def test_list_assignments_module_not_found(client: AsyncClient) -> None:
    """GET /assignments/?module_id= returns 404 for an unknown module."""
    response = await client.get("/assignments/?module_id=does-not-exist")
    assert response.status_code == 404
