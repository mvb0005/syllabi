"""Tests for the POST /courses/{course_id}/enroll endpoint."""

import uuid

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_and_login(
    client: AsyncClient,
    *,
    role: str = "student",
    password: str = "secret",
) -> dict[str, str]:
    """Create a user, log in, and return ``{"id": ..., "email": ...}``.

    The client's cookie jar will contain the ``access_token`` after this call.
    """
    email = f"{uuid.uuid4()}@enroll-test.com"
    resp = await client.post(
        "/users/",
        json={"email": email, "full_name": "User", "role": role, "password": password},
    )
    assert resp.status_code == 201, resp.text
    user_id: str = resp.json()["id"]
    login = await client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"id": user_id, "email": email}


async def _make_course(client: AsyncClient) -> str:
    """Create a course as the currently authenticated instructor and return course_id."""
    resp = await client.post(
        "/courses/", json={"title": f"Course {uuid.uuid4()}", "description": ""}
    )
    assert resp.status_code == 201, resp.text
    return str(resp.json()["id"])


# ---------------------------------------------------------------------------
# Enrollment tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_student_self_enroll(client: AsyncClient) -> None:
    """A student can self-enroll in a course — returns 201 with enrollment data."""
    instructor_info = await _make_and_login(client, role="instructor")
    course_id = await _make_course(client)

    student_info = await _make_and_login(client, role="student")
    resp = await client.post(f"/courses/{course_id}/enroll", json={})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["student_id"] == student_info["id"]
    assert data["course_id"] == course_id
    assert "enrolled_at" in data
    _ = instructor_info  # referenced above


@pytest.mark.asyncio
async def test_enroll_duplicate_returns_409(client: AsyncClient) -> None:
    """Enrolling the same student twice returns 409."""
    await _make_and_login(client, role="instructor")
    course_id = await _make_course(client)

    await _make_and_login(client, role="student")
    resp1 = await client.post(f"/courses/{course_id}/enroll", json={})
    assert resp1.status_code == 201, resp1.text

    resp2 = await client.post(f"/courses/{course_id}/enroll", json={})
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_enroll_non_existent_course_returns_404(client: AsyncClient) -> None:
    """Enrolling in a non-existent course returns 404."""
    await _make_and_login(client, role="student")
    resp = await client.post("/courses/does-not-exist/enroll", json={})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_enroll_returns_401(client: AsyncClient) -> None:
    """Enrollment without a valid session cookie returns 401."""
    await _make_and_login(client, role="instructor")
    course_id = await _make_course(client)

    # Log out so the cookie is cleared.
    await client.post("/auth/logout")
    resp = await client.post(f"/courses/{course_id}/enroll", json={})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_instructor_enroll_student_by_id(client: AsyncClient) -> None:
    """An instructor can enroll a specific student by providing student_id."""
    # Create a student (not logged in as them).
    student_email = f"{uuid.uuid4()}@stud.com"
    stud_resp = await client.post(
        "/users/",
        json={"email": student_email, "full_name": "S", "role": "student", "password": "pw"},
    )
    assert stud_resp.status_code == 201
    student_id: str = stud_resp.json()["id"]

    # Create and log in as an instructor, then create a course.
    instructor_email = f"{uuid.uuid4()}@inst.com"
    await client.post(
        "/users/",
        json={
            "email": instructor_email,
            "full_name": "I",
            "role": "instructor",
            "password": "pw",
        },
    )
    await client.post("/auth/login", json={"email": instructor_email, "password": "pw"})
    course_resp = await client.post(
        "/courses/", json={"title": f"C-{uuid.uuid4()}", "description": ""}
    )
    assert course_resp.status_code == 201
    course_id: str = course_resp.json()["id"]

    resp = await client.post(f"/courses/{course_id}/enroll", json={"student_id": student_id})
    assert resp.status_code == 201, resp.text
    assert resp.json()["student_id"] == student_id
