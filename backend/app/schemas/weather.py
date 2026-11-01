"""Weather data schemas (Phase 3 placeholder)."""

from datetime import datetime

from pydantic import BaseModel


class WeatherForecast(BaseModel):
    """Schema for weather forecast data."""

    location: str
    latitude: float
    longitude: float
    period: str  # e.g., "today", "3-day"
    temperature_max: float | None = None
    temperature_min: float | None = None
    precipitation_mm: float | None = None
    source: str = "Open-Meteo"
    retrieved_at: datetime | None = None
