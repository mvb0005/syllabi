"""Typed custom exception hierarchy for the LMS backend."""


class LMSError(Exception):
    """Base class for all application-level exceptions."""


class NotFoundError(LMSError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, resource_id: str) -> None:
        """Initialise with the resource type and identifier."""
        super().__init__(f"{resource} '{resource_id}' not found")
        self.resource = resource
        self.resource_id = resource_id


class ConflictError(LMSError):
    """Raised when a create/update request would violate a uniqueness constraint."""

    def __init__(self, detail: str) -> None:
        """Initialise with a human-readable conflict description."""
        super().__init__(detail)
        self.detail = detail


class PermissionError(LMSError):
    """Raised when the current user lacks permission for the requested action."""

    def __init__(self, detail: str = "Permission denied") -> None:
        """Initialise with an optional detail string."""
        super().__init__(detail)
        self.detail = detail


class GradingError(LMSError):
    """Raised when the grading pipeline encounters an unrecoverable error."""

    def __init__(self, detail: str) -> None:
        """Initialise with a description of the grading failure."""
        super().__init__(detail)
        self.detail = detail
