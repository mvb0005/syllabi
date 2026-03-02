# Phase 3A — JWT Authentication (Agent Implementation Spec)

## Goal
Implement cookie-based JWT authentication for the LMS FastAPI backend.
Replace the `get_current_user` stub that currently raises `NotImplementedError`.

---

## Project Layout (relevant paths)

```
backend/
  config.py           # Settings via pydantic-settings; add JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
  dependencies.py     # get_current_user lives here — implement it
  exceptions.py       # Add AuthenticationError, AuthorizationError
  main.py             # Register the new auth router
  models/
    user.py           # User model already exists; has hashed_password: str, role: str
  routers/
    auth.py           # CREATE THIS — login, logout, me endpoints
  schemas/
    user.py           # UserPublic already exists; add LoginRequest schema
  services/
    user_service.py   # Already has get_user_by_email; add verify_password helper
  tests/
    routers/
      test_auth.py    # CREATE THIS — all auth tests
```

---

## Implementation Tasks

### 1. Dependencies — `backend/requirements.txt`
Add:
```
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
```

### 2. Settings — `backend/config.py`
Add to the existing `Settings` class:
```python
JWT_SECRET: str = "change-me-in-production"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
```

### 3. Schemas — `backend/schemas/user.py`
Add:
```python
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenPayload(BaseModel):
    sub: str        # user id as string
    role: str
    exp: int
```

### 4. Exceptions — `backend/exceptions.py`
Add:
```python
class AuthenticationError(Exception):
    """Raised when credentials are invalid or token cannot be decoded."""

class AuthorizationError(Exception):
    """Raised when a user lacks the required role."""
```

### 5. Auth Router — `backend/routers/auth.py` (CREATE)
```python
POST /auth/login
  - Body: LoginRequest (email, password)
  - Load user by email; verify bcrypt password via passlib
  - On success: create JWT, set as httpOnly cookie named "access_token", return UserPublic
  - On failure: raise HTTP 401

POST /auth/logout
  - Delete "access_token" cookie
  - Return {"message": "logged out"}

GET /auth/me
  - Depends on get_current_user
  - Return UserPublic for the authenticated user
```

Cookie must be set as:
```python
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    samesite="lax",
    secure=False,   # set True in production
    max_age=settings.JWT_EXPIRE_MINUTES * 60,
)
```

### 6. Dependency — `backend/dependencies.py`
Implement `get_current_user`:
```python
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

Add role-guard helpers:
```python
async def instructor_required(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access required")
    return current_user

async def student_required(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    return current_user
```

### 7. Wire instructor_id — `backend/routers/courses.py`
- Remove `instructor_id` from `CourseCreate` schema
- Inject `current_user: User = Depends(instructor_required)` on `POST /courses/`
- Set `instructor_id = current_user.id` in the service call

### 8. Register router — `backend/main.py`
```python
from backend.routers.auth import router as auth_router
app.include_router(auth_router, prefix="/auth", tags=["auth"])
```

---

## Test File — `backend/tests/routers/test_auth.py`

Use the existing `conftest.py` async client pattern. Cover:

| Test | Expected |
|---|---|
| `test_login_success` | 200 + `Set-Cookie: access_token` |
| `test_login_wrong_password` | 401 |
| `test_login_unknown_email` | 401 |
| `test_logout_clears_cookie` | 200 + cookie cleared |
| `test_me_authenticated` | 200 + UserPublic body |
| `test_me_unauthenticated` | 401 |
| `test_instructor_endpoint_with_student_token` | 403 |
| `test_instructor_endpoint_with_instructor_token` | 200 |

---

## Acceptance Criteria

- `ruff check backend/ && ruff format --check backend/` passes
- `mypy --strict backend/` passes
- `pytest backend/tests/` passes (all tests, including existing ones)
- Login returns 200 with `Set-Cookie: access_token=...; HttpOnly`
- Invalid credentials return 401
- Protected route without cookie returns 401
- Instructor-only route with student cookie returns 403
- `get_current_user` no longer raises `NotImplementedError`

---

## Constraints

- Never store tokens in responses bodies intended for `localStorage`
- Use `httpOnly` cookies exclusively
- All functions must have full type annotations — `mypy --strict` must pass
- Google-style docstrings on all public functions
- Do NOT implement enrollment or grading logic — those are Phase 3B and 3C
