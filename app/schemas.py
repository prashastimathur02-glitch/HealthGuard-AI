from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserProfile:
    age_group: str
    health_condition: str
    occupation: str
    gender: str = "Prefer not to say"


@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    country: str = ""


@dataclass(frozen=True)
class Conditions:
    observed_at: str
    temperature_c: Optional[float]
    relative_humidity: Optional[int]
    apparent_temperature_c: Optional[float]
    wind_speed_kmh: Optional[float]
    precipitation_mm: Optional[float]
    weather_code: Optional[int]
    aqi_us: Optional[int]
    pm2_5: Optional[float]
    pm10: Optional[float]
    uv_index: Optional[float]


@dataclass(frozen=True)
class RiskAssessment:
    level: str
    score: int
    reasons: list[str]
    actions: list[str]
