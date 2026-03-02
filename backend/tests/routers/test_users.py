"""Tests for the /users router."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient) -> None:
    """POST /users/ creates a user and returns 201."""
    response = await client.post(
        "/users/",
        json={
            "email": "alice@example.com",
            "full_name": "Alice",
            "role": "student",
            "password": "secret123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice"
    assert "hashed_password" not in data
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_user_returns_409(client: AsyncClient) -> None:
    """POST /users/ with duplicate email returns 409."""
    payload = {
        "email": "bob@example.com",
        "full_name": "Bob",
        "role": "student",
        "password": "secret123",
    }
    await client.post("/users/", json=payload)
    response = await client.post("/users/", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient) -> None:
    """GET /users/{id} returns 404 for unknown ID."""
    response = await client.get("/users/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient) -> None:
    """GET /users/{id} returns the user."""
    create_resp = await client.post(
        "/users/",
        json={
            "email": "charlie@example.com",
            "full_name": "Charlie",
            "role": "instructor",
            "password": "pass",
        },
    )
    user_id = create_resp.json()["id"]
    response = await client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id
