"""Tests for the /execute router (compile-service proxy)."""

from typing import Self

import httpx
import pytest
from httpx import AsyncClient


class _StubAsyncClient:
    """Stands in for httpx.AsyncClient so no compile service is needed."""

    response: httpx.Response = httpx.Response(200, json={"ok": True, "js": "export {}"})
    raises: Exception | None = None
    last_json: dict[str, str] | None = None

    def __init__(self, **_kwargs: object) -> None:
        pass

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        return None

    async def post(self, _url: str, **kwargs: object) -> httpx.Response:
        _StubAsyncClient.last_json = kwargs.get("json")  # type: ignore[assignment]
        if self.raises is not None:
            raise self.raises
        return self.response


@pytest.fixture
def stub_compiler(monkeypatch: pytest.MonkeyPatch) -> type[_StubAsyncClient]:
    """Patch the execute router's AsyncClient with a controllable stub."""
    _StubAsyncClient.response = httpx.Response(200, json={"ok": True, "js": "export {}"})
    _StubAsyncClient.raises = None
    monkeypatch.setattr(httpx, "AsyncClient", _StubAsyncClient)
    return _StubAsyncClient


@pytest.mark.asyncio
async def test_compile_cpp_ok(client: AsyncClient, stub_compiler: type[_StubAsyncClient]) -> None:
    """POST /execute/cpp relays a successful compile."""
    resp = await client.post("/execute/cpp", json={"source": "int main(){}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["js"] == "export {}"


@pytest.mark.asyncio
async def test_compile_cpp_diagnostics(
    client: AsyncClient, stub_compiler: type[_StubAsyncClient]
) -> None:
    """POST /execute/cpp relays compiler diagnostics on failure."""
    stub_compiler.response = httpx.Response(
        200, json={"ok": False, "diagnostics": "error: expected ';'"}
    )
    resp = await client.post("/execute/cpp", json={"source": "int main( bad"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "expected" in body["diagnostics"]


@pytest.mark.asyncio
async def test_compile_cpp_service_down(
    client: AsyncClient, stub_compiler: type[_StubAsyncClient]
) -> None:
    """POST /execute/cpp maps a connection failure to 503."""
    stub_compiler.raises = httpx.ConnectError("refused")
    resp = await client.post("/execute/cpp", json={"source": "int main(){}"})
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_compile_cpp_rejects_empty_and_oversize(client: AsyncClient) -> None:
    """POST /execute/cpp validates the source length bounds."""
    assert (await client.post("/execute/cpp", json={"source": ""})).status_code == 422
    huge = "x" * 100_001
    assert (await client.post("/execute/cpp", json={"source": huge})).status_code == 422


async def _make_milestone(client: AsyncClient) -> str:
    """Create a course/module/assignment with a hidden test harness."""
    import uuid

    email = f"instructor-{uuid.uuid4()}@execute-test.com"
    resp = await client.post(
        "/users/",
        json={"email": email, "full_name": "I", "role": "instructor", "password": "pw"},
    )
    assert resp.status_code == 201
    assert (
        await client.post("/auth/login", json={"email": email, "password": "pw"})
    ).status_code == 200
    course = await client.post("/courses/", json={"title": "C"})
    module = await client.post(f"/courses/{course.json()['id']}/modules", json={"title": "M"})
    assignment = await client.post(
        "/assignments/",
        params={"module_id": module.json()["id"]},
        json={
            "title": "milestone",
            "starter_code": "int stub();",
            "test_code": "// HIDDEN-HARNESS int main(){}",
        },
    )
    assert assignment.status_code == 201
    return str(assignment.json()["id"])


@pytest.mark.asyncio
async def test_compile_cpp_appends_assignment_harness(
    client: AsyncClient, stub_compiler: type[_StubAsyncClient]
) -> None:
    """POST /execute/cpp with assignment_id compiles source + hidden harness."""
    assignment_id = await _make_milestone(client)
    resp = await client.post(
        "/execute/cpp", json={"source": "int stub(){return 1;}", "assignment_id": assignment_id}
    )
    assert resp.status_code == 200
    sent = stub_compiler.last_json
    assert sent is not None
    assert sent["source"].startswith("int stub(){return 1;}")
    assert "HIDDEN-HARNESS" in sent["source"]


@pytest.mark.asyncio
async def test_compile_cpp_unknown_assignment(
    client: AsyncClient, stub_compiler: type[_StubAsyncClient]
) -> None:
    """POST /execute/cpp 404s for an unknown assignment_id."""
    resp = await client.post(
        "/execute/cpp", json={"source": "int main(){}", "assignment_id": "nope"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assignment_public_hides_test_code(client: AsyncClient) -> None:
    """test_code never appears in any assignment API response."""
    assignment_id = await _make_milestone(client)
    resp = await client.get(f"/assignments/{assignment_id}")
    assert resp.status_code == 200
    assert "test_code" not in resp.json()
    assert "HIDDEN-HARNESS" not in resp.text
