"""Mandi price data schemas (Phase 3 placeholder)."""

from datetime import datetime

from pydantic import BaseModel


class MandiPriceRecord(BaseModel):
    """Schema for individual mandi price arrival."""

    commodity: str
    variety: str | None = None
    market: str
    district: str
    state: str
    min_price: float | None = None
    max_price: float | None = None
    modal_price: float | None = None
    unit: str = "Rs/Quintal"
    arrival_date: str | None = None
    source_url: str | None = None
    retrieved_at: datetime | None = None
