"""Tests for the /auth router (login, logout, me)."""

import uuid

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user(
    client: AsyncClient,
    *,
    role: str = "student",
    password: str = "secret123",
) -> dict[str, object]:
    """Register a new user and return the JSON response body."""
    resp = await client.post(
        "/users/",
        json={
            "email": f"{uuid.uuid4()}@test.com",
            "full_name": "Test User",
            "role": role,
            "password": password,
        },
    )
    assert resp.status_code == 201, resp.text
    return dict(resp.json())


async def _login(
    client: AsyncClient,
    email: str,
    password: str,
) -> int:
    """POST /auth/login and return the HTTP status code.

    The client's cookie jar is updated automatically by httpx on success.
    """
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    return resp.status_code


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """POST /auth/login with correct credentials returns 200 and sets httpOnly cookie."""
    user = await _create_user(client, role="student", password="correct")
    resp = await client.post("/auth/login", json={"email": user["email"], "password": "correct"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == user["email"]
    assert "hashed_password" not in body

    set_cookie = resp.headers.get("set-cookie", "")
    assert "access_token" in set_cookie
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """POST /auth/login with wrong password returns 401."""
    user = await _create_user(client, password="correct")
    resp = await client.post("/auth/login", json={"email": user["email"], "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient) -> None:
    """POST /auth/login with unknown email returns 401."""
    resp = await client.post("/auth/login", json={"email": "nobody@nowhere.com", "password": "x"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logout_clears_cookie(client: AsyncClient) -> None:
    """POST /auth/logout returns 200 and deletes the access_token cookie."""
    user = await _create_user(client, password="pw")
    await _login(client, str(user["email"]), "pw")

    resp = await client.post("/auth/logout")
    assert resp.status_code == 200
    assert resp.json() == {"message": "logged out"}

    set_cookie = resp.headers.get("set-cookie", "")
    # Cookie should be cleared (max-age=0 or expires in the past)
    assert "access_token" in set_cookie
    assert "max-age=0" in set_cookie.lower() or "expires=" in set_cookie.lower()


# ---------------------------------------------------------------------------
# GET /auth/me tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient) -> None:
    """GET /auth/me without a cookie returns 401."""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient) -> None:
    """GET /auth/me after login returns the authenticated user's profile."""
    user = await _create_user(client, role="instructor", password="pw")
    await _login(client, str(user["email"]), "pw")

    resp = await client.get("/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == user["email"]
    assert body["id"] == user["id"]
    assert "hashed_password" not in body


# ---------------------------------------------------------------------------
# Role guard tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_instructor_endpoint_with_student_cookie(client: AsyncClient) -> None:
    """POST /courses/ with a student token returns 403."""
    student = await _create_user(client, role="student", password="pw")
    await _login(client, str(student["email"]), "pw")

    resp = await client.post("/courses/", json={"title": "CS101", "description": ""})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_instructor_endpoint_with_instructor_cookie(client: AsyncClient) -> None:
    """POST /courses/ with an instructor token returns 201."""
    instructor = await _create_user(client, role="instructor", password="pw")
    await _login(client, str(instructor["email"]), "pw")

    resp = await client.post("/courses/", json={"title": "CS101", "description": "Intro course"})
    assert resp.status_code == 201
    assert resp.json()["instructor_id"] == instructor["id"]


@pytest.mark.asyncio
async def test_protected_endpoint_without_cookie(client: AsyncClient) -> None:
    """POST /courses/ without any cookie returns 401."""
    resp = await client.post("/courses/", json={"title": "CS101"})
    assert resp.status_code == 401
