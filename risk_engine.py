
import pandas as pd

def build_trend_dataframe(weather_json: dict, air_json: dict) -> pd.DataFrame:
    w = weather_json["hourly"]
    a = air_json["hourly"]
    df_w = pd.DataFrame({
        "time": pd.to_datetime(w["time"]),
        "temperature_2m": w["temperature_2m"],
        "relative_humidity_2m": w["relative_humidity_2m"],
        "precipitation": w["precipitation"],
        "uv_index": w["uv_index"],
        "wind_speed_10m": w["wind_speed_10m"],
    })
    df_a = pd.DataFrame({
        "time": pd.to_datetime(a["time"]),
        "pm2_5": a["pm2_5"], "pm10": a["pm10"], "us_aqi": a["us_aqi"],
    })
    df = pd.merge(df_w, df_a, on="time", how="inner")
    df["date"] = df["time"].dt.date
    return df.groupby("date").mean(numeric_only=True).reset_index()


def rule_based_advisory(profile: dict, c: dict) -> str:
    lines = []
    aqi = c["us_aqi"]; uv = c["uv_index"]; temp = c["temperature"]
    condition = profile["health_condition"]; occupation = profile["occupation"]; age_group = profile["age_group"]

    if aqi is not None:
        if aqi > 150:
            lines.append(f"Air quality is unhealthy right now (US AQI {aqi:.0f}).")
            if condition == "Asthma":
                lines.append("With asthma, avoid outdoor exertion and keep a reliever inhaler on hand.")
            if occupation == "Outdoor worker":
                lines.append("If you must work outside, wear an N95 mask and take frequent indoor breaks.")
        elif aqi > 100:
            lines.append(f"Air quality is moderate-to-poor (US AQI {aqi:.0f}); sensitive groups should limit prolonged outdoor exertion.")
        else:
            lines.append(f"Air quality is acceptable today (US AQI {aqi:.0f}).")

    if uv is not None and uv >= 6:
        lines.append(f"UV index is high ({uv:.0f}); use sunscreen and sunglasses if you're outdoors, especially for {occupation.lower()} tasks.")

    if temp is not None and temp >= 35:
        lines.append(f"It's very hot ({temp:.0f}°C) — stay hydrated and avoid peak-heat hours.")
        if age_group in ("Child", "Senior (60+)"):
            lines.append(f"{age_group}s are more heat-sensitive, so extra caution is recommended.")

    if not lines:
        lines.append("Conditions look generally fine today — no major precautions needed for your profile.")
    return " ".join(lines)

def calculate_risk_score(profile: dict, conditions: dict) -> int:
    """
    Calculate a simple personalized environmental risk score from 0 to 100.
    Higher score means higher environmental risk.
    """

    score = 0

    aqi = conditions.get("us_aqi")
    temp = conditions.get("temperature")
    uv = conditions.get("uv_index")

    age_group = profile.get("age_group")
    health_condition = profile.get("health_condition")
    occupation = profile.get("occupation")

    # Air quality
    if aqi is not None:
        if aqi > 300:
            score += 50
        elif aqi > 200:
            score += 40
        elif aqi > 150:
            score += 30
        elif aqi > 100:
            score += 20
        elif aqi > 50:
            score += 10

    # Heat
    if temp is not None:
        if temp >= 40:
            score += 25
        elif temp >= 35:
            score += 20
        elif temp >= 30:
            score += 10

    # UV exposure
    if uv is not None:
        if uv >= 8:
            score += 10
        elif uv >= 6:
            score += 5

    # Higher-risk age groups
    if age_group in ("Child", "Senior (60+)"):
        score += 5

    # Health conditions
    if health_condition in (
        "Asthma",
        "Heart condition",
        "Other respiratory condition"
    ):
        score += 10
    elif health_condition in ("Allergies", "Pregnant"):
        score += 5

    # Outdoor exposure
    if occupation in (
        "Outdoor worker",
        "Athlete / frequent exerciser"
    ):
        score += 10

    return min(score, 100)

if __name__ == "__main__":
    test_profile = {
        "age_group": "Senior (60+)",
        "health_condition": "Asthma",
        "occupation": "Outdoor worker"
    }

    test_conditions = {
        "us_aqi": 185,
        "temperature": 34,
        "uv_index": 7
    }

    print("Risk score:", calculate_risk_score(test_profile, test_conditions))