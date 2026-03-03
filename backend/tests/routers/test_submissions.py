"""Tests for the /submissions router with enrollment enforcement."""

import uuid

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register_and_login(
    client: AsyncClient,
    *,
    role: str = "student",
    password: str = "pw123",
) -> dict[str, str]:
    """Register a user, log them in, and return ``{"id": ..., "email": ...}``.

    The client's cookie jar will contain ``access_token`` after this call.
    """
    email = f"{uuid.uuid4()}@sub-test.com"
    resp = await client.post(
        "/users/",
        json={"email": email, "full_name": "User", "role": role, "password": password},
    )
    assert resp.status_code == 201, resp.text
    login = await client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"id": str(resp.json()["id"]), "email": email}


async def _setup_course_with_assignment(client: AsyncClient) -> dict[str, str]:
    """Create an instructor → course → module → assignment chain.

    Returns a dict with keys: ``course_id``, ``module_id``, ``assignment_id``.
    The client is still authenticated as the instructor after this call.
    """
    await _register_and_login(client, role="instructor")

    course_resp = await client.post(
        "/courses/", json={"title": f"C-{uuid.uuid4()}", "description": ""}
    )
    assert course_resp.status_code == 201, course_resp.text
    course_id: str = course_resp.json()["id"]

    module_resp = await client.post(
        f"/courses/{course_id}/modules",
        json={"title": "Module 1", "order_index": 0, "content_md": ""},
    )
    assert module_resp.status_code == 201, module_resp.text
    module_id: str = module_resp.json()["id"]

    assignment_resp = await client.post(
        "/assignments/",
        params={"module_id": module_id},
        json={"title": "HW1", "description_md": "", "grading_type": "deterministic"},
    )
    assert assignment_resp.status_code == 201, assignment_resp.text
    assignment_id: str = assignment_resp.json()["id"]

    return {"course_id": course_id, "module_id": module_id, "assignment_id": assignment_id}


# ---------------------------------------------------------------------------
# Submission tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submit_without_enrollment_returns_403(client: AsyncClient) -> None:
    """A student who is NOT enrolled gets 403 when submitting."""
    ids = await _setup_course_with_assignment(client)
    await _register_and_login(client, role="student")

    resp = await client.post(
        "/submissions/",
        json={"assignment_id": ids["assignment_id"], "content": "my answer"},
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_submit_with_enrollment_creates_submission(client: AsyncClient) -> None:
    """An enrolled student can submit and receives 201."""
    ids = await _setup_course_with_assignment(client)
    student_info = await _register_and_login(client, role="student")

    # Enroll the student.
    enroll = await client.post(f"/courses/{ids['course_id']}/enroll", json={})
    assert enroll.status_code == 201, enroll.text

    resp = await client.post(
        "/submissions/",
        json={"assignment_id": ids["assignment_id"], "content": "my answer"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["student_id"] == student_info["id"]
    assert data["assignment_id"] == ids["assignment_id"]


@pytest.mark.asyncio
async def test_submit_as_instructor_returns_403(client: AsyncClient) -> None:
    """Instructors are not students — POST /submissions/ requires student role."""
    ids = await _setup_course_with_assignment(client)
    # Still authenticated as instructor from setup.

    resp = await client.post(
        "/submissions/",
        json={"assignment_id": ids["assignment_id"], "content": "cheating"},
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_submit_unauthenticated_returns_401(client: AsyncClient) -> None:
    """Submitting without a session cookie returns 401."""
    ids = await _setup_course_with_assignment(client)
    await client.post("/auth/logout")

    resp = await client.post(
        "/submissions/",
        json={"assignment_id": ids["assignment_id"], "content": "anon"},
    )
    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_submit_bad_assignment_returns_404(client: AsyncClient) -> None:
    """After enrolment, submitting to non-existent assignment returns 404."""
    ids = await _setup_course_with_assignment(client)
    await _register_and_login(client, role="student")

    await client.post(f"/courses/{ids['course_id']}/enroll", json={})

    resp = await client.post(
        "/submissions/",
        json={"assignment_id": "no-such-assignment", "content": "x"},
    )
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# Grade access tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_grade_unauthenticated_returns_401(client: AsyncClient) -> None:
    """GET /submissions/{id}/grade without auth returns 401."""
    ids = await _setup_course_with_assignment(client)
    student_info = await _register_and_login(client, role="student")
    await client.post(f"/courses/{ids['course_id']}/enroll", json={})
    sub_resp = await client.post(
        "/submissions/",
        json={"assignment_id": ids["assignment_id"], "content": "a"},
    )
    assert sub_resp.status_code == 201
    sub_id: str = sub_resp.json()["id"]

    await client.post("/auth/logout")
    resp = await client.get(f"/submissions/{sub_id}/grade")
    assert resp.status_code == 401, resp.text
    _ = student_info


@pytest.mark.asyncio
async def test_get_grade_wrong_student_returns_403(client: AsyncClient) -> None:
    """Another student cannot view someone else's grade."""
    ids = await _setup_course_with_assignment(client)

    # Student A submits.
    await _register_and_login(client, role="student")
    await client.post(f"/courses/{ids['course_id']}/enroll", json={})
    sub_resp = await client.post(
        "/submissions/",
        json={"assignment_id": ids["assignment_id"], "content": "a"},
    )
    assert sub_resp.status_code == 201
    sub_id: str = sub_resp.json()["id"]

    # Student B tries to view the grade.
    await _register_and_login(client, role="student")
    resp = await client.get(f"/submissions/{sub_id}/grade")
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_get_grade_owner_returns_404_before_grading(client: AsyncClient) -> None:
    """The submitting student can query the grade endpoint (returns 404, not 403)."""
    ids = await _setup_course_with_assignment(client)
    await _register_and_login(client, role="student")
    await client.post(f"/courses/{ids['course_id']}/enroll", json={})
    sub_resp = await client.post(
        "/submissions/",
        json={"assignment_id": ids["assignment_id"], "content": "a"},
    )
    assert sub_resp.status_code == 201
    sub_id: str = sub_resp.json()["id"]

    resp = await client.get(f"/submissions/{sub_id}/grade")
    # No grade record yet → 404, but NOT 403 (ownership confirmed).
    assert resp.status_code == 404, resp.text


@pytest.mark.asyncio
async def test_get_grade_instructor_returns_404_before_grading(client: AsyncClient) -> None:
    """An instructor can query any grade (returns 404 before grading, not 403)."""
    ids = await _setup_course_with_assignment(client)
    student_info = await _register_and_login(client, role="student")
    await client.post(f"/courses/{ids['course_id']}/enroll", json={})
    sub_resp = await client.post(
        "/submissions/",
        json={"assignment_id": ids["assignment_id"], "content": "a"},
    )
    assert sub_resp.status_code == 201
    sub_id: str = sub_resp.json()["id"]

    # Re-login as an instructor.
    await _register_and_login(client, role="instructor")
    resp = await client.get(f"/submissions/{sub_id}/grade")
    assert resp.status_code == 404, resp.text
    _ = student_info
