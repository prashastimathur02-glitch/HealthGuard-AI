from __future__ import annotations

import sqlite3
from pathlib import Path

from app.schemas import Conditions, Location, RiskAssessment, UserProfile

DB_PATH = Path("weather_advisory.db")


def initialize() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS advisory_history (
            id INTEGER PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            location TEXT, aqi INTEGER, temperature REAL, risk_level TEXT,
            profile TEXT, advisory TEXT)""")


def save_advisory(location: Location, profile: UserProfile, conditions: Conditions, risk: RiskAssessment, advisory: str) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "INSERT INTO advisory_history (location, aqi, temperature, risk_level, profile, advisory) VALUES (?, ?, ?, ?, ?, ?)",
            (location.name, conditions.aqi_us, conditions.temperature_c, risk.level, f"{profile.age_group}; {profile.health_condition}; {profile.occupation}", advisory),
        )


def recent_advisories(location_name: str, limit: int = 7) -> list[dict[str, object]]:
    """Return locally saved snapshots so history remains available after refreshes."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT created_at, aqi, temperature, risk_level, profile FROM advisory_history WHERE location = ? ORDER BY id DESC LIMIT ?",
            (location_name, limit),
        ).fetchall()
    return [dict(row) for row in rows]
