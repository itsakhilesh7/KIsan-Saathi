"""Crop advisory response schemas (Phase 4 placeholder)."""

from pydantic import BaseModel, Field

from .evidence import Evidence


class AdvisoryResponse(BaseModel):
    """Crop advisory response grounded in retrieved KCC records."""

    query: str
    answer: str
    sources: list[Evidence] = Field(default_factory=list)
    confidence_note: str | None = None
