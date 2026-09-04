from __future__ import annotations

import os
import requests

from app.risk_engine import aqi_band
from app.schemas import Conditions, RiskAssessment, UserProfile


def deterministic_advisory(profile: UserProfile, conditions: Conditions, risk: RiskAssessment) -> str:
    aqi_text = "AQI is currently unavailable" if conditions.aqi_us is None else f"the AQI is {conditions.aqi_us} ({aqi_band(conditions.aqi_us).lower()})"
    return f"Your current risk is **{risk.level.lower()}**: {aqi_text}. For a {profile.age_group.lower()} who is a {profile.occupation.lower()}, focus on: {'; '.join(risk.actions)}"


def generate_advisory(profile: UserProfile, conditions: Conditions, risk: RiskAssessment) -> tuple[str, str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return deterministic_advisory(profile, conditions, risk), "Rules-based advisory (add GROQ_API_KEY for AI wording)"
    facts = {"profile": profile.__dict__, "conditions": conditions.__dict__, "risk": risk.__dict__}
    prompt = "Write a concise, plain-English weather and AQI advisory in 55 words or fewer. Use only supplied facts. Do not diagnose or add numbers. End with informational-not-medical-advice disclaimer. Facts: " + str(facts)
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 150}, timeout=15)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip(), "AI-personalized advisory"
    except (requests.RequestException, KeyError, ValueError):
        return deterministic_advisory(profile, conditions, risk), "Rules-based fallback (AI temporarily unavailable)"


def daily_outlook_advisory(profile: UserProfile, hourly_risks: list[RiskAssessment], outlook: list[Conditions]) -> str:
    if not outlook:
        return "A full-day forecast is not available right now. Please check the live advisory again later."
    peak = max(hourly_risks, key=lambda item: item.score)
    peak_index = hourly_risks.index(peak)
    peak_hour = outlook[peak_index].observed_at[11:16]
    safe_hours = [item.observed_at[11:16] for item, risk in zip(outlook, hourly_risks) if risk.level == "Low"]
    safest = f"Lower-risk hours include {', '.join(safe_hours[:3])}" if safe_hours else "No clearly low-risk outdoor window is forecast"
    return f"Today’s highest expected personal risk is **{peak.level.lower()}** around {peak_hour}. {safest}. Plan strenuous outdoor activity for lower-risk hours, and reassess if you develop symptoms."


def tomorrow_outlook_advisory(hourly_risks: list[RiskAssessment], outlook: list[Conditions]) -> str:
    """Give one proactive, easily understood next-day planning message."""
    if not outlook:
        return "Tomorrow’s forecast is not available yet."
    today = outlook[0].observed_at[:10]
    tomorrow_pairs = [(condition, risk) for condition, risk in zip(outlook, hourly_risks) if condition.observed_at[:10] > today]
    if not tomorrow_pairs:
        return "Tomorrow’s forecast window is not available yet."
    peak_condition, peak_risk = max(tomorrow_pairs, key=lambda pair: pair[1].score)
    lowest_score = min(risk.score for _, risk in tomorrow_pairs)
    safest = [condition.observed_at[11:16] for condition, risk in tomorrow_pairs if risk.score == lowest_score][:3]
    return (
        f"Plan ahead: tomorrow’s highest expected risk is **{peak_risk.level.lower()}** around "
        f"{peak_condition.observed_at[11:16]}. Lower-risk times include {', '.join(safest)}."
    )


def translate_text(text: str, language: str) -> tuple[str, str]:
    if language == "English":
        return text, "English"
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return text, "English fallback — add GROQ_API_KEY to translate"
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), "messages": [{"role": "user", "content": f"Translate this health advisory into {language}. Preserve all facts, warnings, formatting, and disclaimer. Do not add advice: {text}"}], "temperature": 0, "max_tokens": 250},
            timeout=15,
        )
        return response.json()["choices"][0]["message"]["content"].strip(), language
    except (requests.RequestException, KeyError, ValueError):
        return text, "English fallback — translation temporarily unavailable"
