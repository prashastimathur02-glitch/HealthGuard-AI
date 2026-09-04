from __future__ import annotations

from app.schemas import Conditions, RiskAssessment, UserProfile


def aqi_band(aqi: int | None) -> str:
    if aqi is None:
        return "Unavailable"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for sensitive groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very unhealthy"
    return "Hazardous"


def _level(score: int) -> str:
    if score >= 7:
        return "Very high"
    if score >= 4:
        return "High"
    if score >= 2:
        return "Moderate"
    return "Low"


def risk_percentage(risk: RiskAssessment) -> int:
    """Convert the transparent 0-12 rule score into a familiar 0-100 display."""
    return min(100, round((risk.score / 12) * 100))


def assess_risk(profile: UserProfile, conditions: Conditions) -> RiskAssessment:
    score, reasons, actions = 0, [], []
    aqi = conditions.aqi_us
    if aqi is None:
        reasons.append("AQI data is unavailable, so pollution-related risk cannot be estimated.")
    elif aqi <= 50:
        reasons.append(f"AQI is {aqi} (good).")
    elif aqi <= 100:
        score += 1
        reasons.append(f"AQI is {aqi} (moderate).")
    elif aqi <= 150:
        score += 2
        reasons.append(f"AQI is {aqi}, which can affect sensitive groups.")
    elif aqi <= 200:
        score += 4
        reasons.append(f"AQI is {aqi} (unhealthy).")
    else:
        score += 6
        reasons.append(f"AQI is {aqi} ({aqi_band(aqi).lower()}).")

    vulnerable = profile.health_condition in {"Asthma", "COPD / heart condition"}
    if vulnerable and aqi is not None and aqi > 50:
        score += 2
        reasons.append(f"{profile.health_condition} increases sensitivity to air pollution.")
    if profile.age_group in {"Infant (0–3)", "Child", "Elderly"} and aqi is not None and aqi > 50:
        score += 1
        reasons.append("This age group can be more affected by poor air quality.")
    if profile.occupation == "Outdoor worker" and aqi is not None and aqi > 50:
        score += 2
        reasons.append("Outdoor work can increase pollution exposure time.")
    if conditions.apparent_temperature_c is not None and conditions.apparent_temperature_c >= 38:
        score += 1
        reasons.append(f"Feels-like temperature is {conditions.apparent_temperature_c:.0f} degrees C.")
        actions.append("Take frequent shade and hydration breaks during outdoor activity.")
    if conditions.uv_index is not None and conditions.uv_index >= 8:
        actions.append("Use sunscreen, cover up, and avoid prolonged midday sun.")
    if aqi is not None and aqi > 100:
        actions.append("Reduce strenuous outdoor activity, especially near traffic.")
    if aqi is not None and aqi > 150 and (vulnerable or profile.occupation == "Outdoor worker"):
        actions.append("Use a well-fitting N95/FFP2 mask if you must be outdoors.")
    if vulnerable and aqi is not None and aqi > 100:
        actions.append("Keep prescribed relief medication accessible and follow your clinician's plan.")
    if not actions:
        actions.append("Normal outdoor activity is reasonable; check again if conditions change.")

    return RiskAssessment(level=_level(score), score=score, reasons=reasons, actions=actions[:3])
