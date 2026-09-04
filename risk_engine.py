
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