"""Pydantic schemas for Source and SourceExcerpt resources."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.models.source import SourceKind


class SourceCreate(BaseModel):
    """Request body for registering a source (instructor only).

    ``path`` is relative to the repository's ``sources/`` directory; absolute
    paths and traversal outside that directory are rejected by the service.
    """

    bibkey: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    authors: str = Field(min_length=1, max_length=500)
    edition: str = ""
    publisher: str = ""
    year: int | None = None
    kind: SourceKind = SourceKind.pdf
    path: str = Field(min_length=1, max_length=500)
    # Printed page = PDF page - page_offset (books number past their front
    # matter); excerpt ranges stay in PDF pages, citations render printed.
    page_offset: int = Field(default=0, ge=0)


class SourcePublic(BaseModel):
    """Source representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    bibkey: str
    title: str
    authors: str
    edition: str
    publisher: str
    year: int | None
    kind: SourceKind
    path: str
    page_offset: int


class SourceExcerptCreate(BaseModel):
    """Request body for embedding a source page range into a module.

    Pages are 1-indexed and inclusive. For ``text`` sources the range is
    interpreted as line numbers.
    """

    module_id: str
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    topic: str = Field(min_length=1, max_length=255)
    context_md: str = ""
    order_index: int = 0

    @model_validator(mode="after")
    def validate_range(self) -> "SourceExcerptCreate":
        """Ensure the page range is well-formed."""
        if self.page_end < self.page_start:
            msg = "page_end must be >= page_start"
            raise ValueError(msg)
        return self


class SourceExcerptPublic(BaseModel):
    """Excerpt representation returned by the API, with its source embedded."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    module_id: str
    page_start: int
    page_end: int
    topic: str
    context_md: str
    order_index: int
    content_text: str
    source: SourcePublic
