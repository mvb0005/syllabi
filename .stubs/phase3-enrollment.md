# Phase 3B — Enrollment & Scoped Access (Agent Implementation Spec)

## Goal
Add a student ↔ course enrollment system and enforce access-scoping rules on submissions
and grading endpoints based on enrollment status.

---

## Dependency on Phase 3A
This branch depends on `get_current_user`, `instructor_required`, and `student_required`
dependencies from Phase 3A (`feat/phase3-auth`). If that branch is not yet merged,
import them from there or stub them locally with the same signatures for development.

---

## Project Layout (relevant paths)

```
backend/
  models/
    enrollment.py     # CREATE THIS
    __init__.py       # export Enrollment
  schemas/
    enrollment.py     # CREATE THIS
  services/
    enrollment_service.py  # CREATE THIS
  routers/
    courses.py        # Add POST /{id}/enroll endpoint
    submissions.py    # Add enrollment check on POST /submissions/
  alembic/versions/
    <new>.py          # Alembic migration for enrollments table
  tests/
    models/
      test_enrollment.py       # CREATE THIS
    routers/
      test_enrollments.py      # CREATE THIS
    services/
      test_enrollment_service.py  # CREATE THIS
```

---

## Implementation Tasks

### 1. Model — `backend/models/enrollment.py` (CREATE)

```python
class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student: Mapped["User"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")

    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_enrollment"),)
```

Update `User` model to add: `enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")`
Update `Course` model to add: `enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")`

### 2. Alembic Migration

Generate a new migration:
```
alembic revision --autogenerate -m "add enrollments table"
```

Verify the generated migration creates the `enrollments` table with:
- `id` SERIAL PRIMARY KEY
- `student_id` INTEGER NOT NULL REFERENCES users(id)
- `course_id` INTEGER NOT NULL REFERENCES courses(id)
- `enrolled_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- UNIQUE constraint on (student_id, course_id)

### 3. Schemas — `backend/schemas/enrollment.py` (CREATE)

```python
class EnrollmentCreate(BaseModel):
    student_id: int | None = None  # omit to self-enroll; required when instructor enrolls another

class EnrollmentPublic(BaseModel):
    id: int
    student_id: int
    course_id: int
    enrolled_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### 4. Service — `backend/services/enrollment_service.py` (CREATE)

```python
async def enroll_student(
    db: AsyncSession,
    course_id: int,
    student_id: int,
) -> Enrollment:
    """Enroll a student in a course. Raises ConflictError if already enrolled."""

async def is_enrolled(
    db: AsyncSession,
    course_id: int,
    student_id: int,
) -> bool:
    """Return True if the student is enrolled in the course."""

async def get_enrollments_for_course(
    db: AsyncSession,
    course_id: int,
) -> list[Enrollment]:
    """Return all enrollments for a given course."""
```

Add a typed `ConflictError` to `backend/exceptions.py`:
```python
class ConflictError(Exception):
    """Raised when a unique constraint would be violated (e.g. duplicate enrollment)."""
```

Map it to HTTP 409 in `main.py`.

### 5. Enroll Endpoint — `backend/routers/courses.py`

```
POST /courses/{course_id}/enroll
```
- Authenticated users only (`get_current_user`)
- If caller is a **student**: enroll themselves (`student_id = current_user.id`)
- If caller is an **instructor**: body must include `student_id` to enroll another user
- On duplicate: return HTTP 409
- On success: return `EnrollmentPublic` with HTTP 201

### 6. Scope Submissions — `backend/routers/submissions.py`

```
POST /submissions/
```
- Must use `student_required` dependency
- Before creating, call `is_enrolled(db, assignment.course_id, current_user.id)`
- If not enrolled: raise HTTP 403 `{"detail": "Not enrolled in this course"}`

```
GET /submissions/{id}/grade
```
- Load submission; load its assignment to get `course_id`
- Allow access if `current_user.id == submission.student_id` OR
  `current_user.id == assignment.course.instructor_id`
- Otherwise: HTTP 403

---

## Test Coverage

### `backend/tests/services/test_enrollment_service.py`
- `test_enroll_student_success`
- `test_enroll_student_duplicate_raises_conflict`
- `test_is_enrolled_true` / `test_is_enrolled_false`

### `backend/tests/routers/test_enrollments.py`
- `test_student_self_enroll_success` → 201
- `test_student_self_enroll_duplicate` → 409
- `test_instructor_enroll_student_success` → 201
- `test_unauthenticated_enroll` → 401

### `backend/tests/routers/test_submissions.py` (extend existing)
- `test_create_submission_enrolled` → 201
- `test_create_submission_not_enrolled` → 403
- `test_get_grade_as_submitter` → 200
- `test_get_grade_as_instructor` → 200
- `test_get_grade_as_other_student` → 403

---

## Acceptance Criteria

- `ruff check backend/ && ruff format --check backend/` passes
- `mypy --strict backend/` passes
- `pytest backend/tests/` passes
- `alembic upgrade head` applies cleanly on a fresh DB
- Unenrolled student receives 403 on `POST /submissions/`
- Enrolled student receives 201 on `POST /submissions/`
- Non-submitter non-instructor receives 403 on `GET /submissions/{id}/grade`
- Duplicate enrollment returns 409

---

## Constraints

- Do NOT implement grading logic — that is Phase 3C
- All functions strictly typed; mypy --strict passes
- Google-style docstrings on all public functions and classes
