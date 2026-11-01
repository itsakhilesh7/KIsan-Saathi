"""Common schema definitions and type aliases."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

LanguageCode = Literal["te-IN", "hi-IN", "en-IN", "hi-en"]


class TimestampMixin(BaseModel):
    """Mixin for UTC timestamping."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
