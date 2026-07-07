"""Course service — business logic for courses, modules, and assignments."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.exceptions import NotFoundError
from backend.models.assignment import Assignment
from backend.models.course import Course, Module
from backend.models.user import User
from backend.schemas.assignment import AssignmentCreate, AssignmentUpdate
from backend.schemas.course import CourseCreate, CourseUpdate, ModuleCreate, ModuleUpdate


class CourseService:
    """Handles course, module, and assignment database operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with an async database session."""
        self._db = db

    async def create_course(self, payload: CourseCreate, *, instructor_id: str) -> Course:
        """Create and persist a new course.

        Args:
            payload: Validated course creation data.
            instructor_id: ID of the instructor who owns the course.

        Returns:
            The newly created Course ORM instance.

        Raises:
            NotFoundError: If no user with ``instructor_id`` exists.
        """
        if await self._db.get(User, instructor_id) is None:
            raise NotFoundError("User", instructor_id)
        course = Course(
            title=payload.title,
            description=payload.description,
            instructor_id=instructor_id,
        )
        self._db.add(course)
        await self._db.commit()
        await self._db.refresh(course)
        return course

    async def list_courses(self) -> list[Course]:
        """Return all courses, most recently created first."""
        result = await self._db.scalars(select(Course).order_by(Course.created_at.desc()))
        return list(result)

    async def get_course(self, course_id: str) -> Course:
        """Retrieve a course by primary key.

        Raises:
            NotFoundError: If no course with that ID exists.
        """
        course = await self._db.get(Course, course_id)
        if course is None:
            raise NotFoundError("Course", course_id)
        return course

    async def update_course(self, course_id: str, payload: CourseUpdate) -> Course:
        """Apply partial updates to a course.

        Raises:
            NotFoundError: If no course with that ID exists.
        """
        course = await self.get_course(course_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(course, field, value)
        await self._db.commit()
        await self._db.refresh(course)
        return course

    async def create_module(self, course_id: str, payload: ModuleCreate) -> Module:
        """Add a module to an existing course.

        Raises:
            NotFoundError: If the parent course does not exist.
        """
        await self.get_course(course_id)
        module = Module(
            course_id=course_id,
            title=payload.title,
            order_index=payload.order_index,
            content_md=payload.content_md,
        )
        self._db.add(module)
        await self._db.commit()
        await self._db.refresh(module)
        return module

    async def update_module(self, course_id: str, module_id: str, payload: ModuleUpdate) -> Module:
        """Apply partial updates to a module of a course.

        Raises:
            NotFoundError: If the module does not exist or belongs to a
                different course.
        """
        module = await self._db.get(Module, module_id)
        if module is None or module.course_id != course_id:
            raise NotFoundError("Module", module_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(module, field, value)
        await self._db.commit()
        await self._db.refresh(module)
        return module

    async def list_modules(self, course_id: str) -> list[Module]:
        """Return a course's modules ordered by ``order_index``.

        Raises:
            NotFoundError: If the course does not exist.
        """
        await self.get_course(course_id)
        result = await self._db.scalars(
            select(Module).where(Module.course_id == course_id).order_by(Module.order_index)
        )
        return list(result)

    async def list_assignments_for_course(self, course_id: str) -> list[Assignment]:
        """Return all assignments across a course's modules.

        Ordered by the parent module's ``order_index``, then creation time,
        so callers can render a whole course without one query per module.

        Raises:
            NotFoundError: If the course does not exist.
        """
        await self.get_course(course_id)
        result = await self._db.scalars(
            select(Assignment)
            .join(Module, Assignment.module_id == Module.id)
            .where(Module.course_id == course_id)
            .order_by(Module.order_index, Assignment.created_at)
        )
        return list(result)

    async def list_assignments(self, module_id: str) -> list[Assignment]:
        """Return a module's assignments ordered by creation time.

        Raises:
            NotFoundError: If the module does not exist.
        """
        if await self._db.get(Module, module_id) is None:
            raise NotFoundError("Module", module_id)
        result = await self._db.scalars(
            select(Assignment)
            .where(Assignment.module_id == module_id)
            .order_by(Assignment.created_at)
        )
        return list(result)

    async def create_assignment(self, module_id: str, payload: AssignmentCreate) -> Assignment:
        """Create an assignment for an existing module.

        Raises:
            NotFoundError: If the parent module does not exist.
        """
        module = await self._db.get(Module, module_id)
        if module is None:
            raise NotFoundError("Module", module_id)
        assignment = Assignment(
            module_id=module_id,
            title=payload.title,
            description_md=payload.description_md,
            grading_type=payload.grading_type,
            max_score=payload.max_score,
            due_at=payload.due_at,
            starter_code=payload.starter_code,
            test_code=payload.test_code,
        )
        self._db.add(assignment)
        await self._db.commit()
        await self._db.refresh(assignment)
        return assignment

    async def get_assignment(self, assignment_id: str) -> Assignment:
        """Retrieve an assignment by primary key.

        Raises:
            NotFoundError: If no assignment with that ID exists.
        """
        assignment = await self._db.get(Assignment, assignment_id)
        if assignment is None:
            raise NotFoundError("Assignment", assignment_id)
        return assignment

    async def update_assignment(self, assignment_id: str, payload: AssignmentUpdate) -> Assignment:
        """Apply partial updates to an assignment.

        Raises:
            NotFoundError: If no assignment with that ID exists.
        """
        assignment = await self.get_assignment(assignment_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(assignment, field, value)
        await self._db.commit()
        await self._db.refresh(assignment)
        return assignment
