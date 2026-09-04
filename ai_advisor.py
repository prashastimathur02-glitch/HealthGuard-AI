import os
from dotenv import load_dotenv
from groq import Groq
from risk_engine import rule_based_advisory

load_dotenv()
_api_key = os.getenv("GROQ_API_KEY")
_client = Groq(api_key=_api_key) if _api_key else None


def build_prompt(profile: dict, c: dict) -> str:
    return (
        f"User profile: age group {profile['age_group']}, "
        f"health condition: {profile['health_condition']}, "
        f"occupation: {profile['occupation']}.\n"
        f"Current conditions: temperature {c['temperature']}°C, humidity {c['humidity']}%, "
        f"UV index {c['uv_index']}, wind {c['wind']} km/h, precipitation {c['precipitation']} mm, "
        f"PM2.5 {c['pm2_5']} µg/m³, PM10 {c['pm10']} µg/m³, US AQI {c['us_aqi']}.\n"
        "Write a short (3-5 sentence), plain-English, personalized health advisory. "
        "Call out specific risks for this person's profile and give concrete precautions "
        "(e.g. mask, hydration, timing outdoor activity, medication reminder if relevant). "
        "Avoid generic disclaimers."
    )


def get_ai_advisory(profile: dict, current_conditions: dict) -> str:
    if _client is None:
        # No key found — fall back so the app never crashes
        return rule_based_advisory(profile, current_conditions)

    try:
        resp = _client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly public health advisor. Give short, plain-English, "
                        "actionable advice tailored to the person's age, health condition, and "
                        "occupation. No medical jargon, no generic disclaimers."
                    ),
                },
                {"role": "user", "content": build_prompt(profile, current_conditions)},
            ],
            temperature=0.6,
            max_tokens=250,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # If the API fails (rate limit, network, etc.) fall back gracefully
        fallback = rule_based_advisory(profile, current_conditions)
        return f"{fallback}\n\n_(AI advisory unavailable right now: {e})_"