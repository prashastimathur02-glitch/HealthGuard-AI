from __future__ import annotations

from typing import Any

import requests

from app.schemas import Conditions, Location

TIMEOUT_SECONDS = 12


class DataProviderError(RuntimeError):
    pass


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as error:
        raise DataProviderError("Live environmental data is currently unavailable.") from error


def search_location(query: str) -> list[Location]:
    payload = _get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": query, "count": 6, "language": "en", "format": "json"},
    )
    return [
        Location(
            name=result["name"],
            latitude=result["latitude"],
            longitude=result["longitude"],
            country=result.get("country", ""),
        )
        for result in payload.get("results", [])
    ]


def fetch_conditions(location: Location) -> Conditions:
    weather = _get_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
    ).get("current", {})
    air = _get_json(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": "us_aqi,pm2_5,pm10,uv_index",
            "timezone": "auto",
        },
    ).get("current", {})
    return Conditions(
        observed_at=weather.get("time", air.get("time", "Unknown")),
        temperature_c=weather.get("temperature_2m"),
        relative_humidity=weather.get("relative_humidity_2m"),
        apparent_temperature_c=weather.get("apparent_temperature"),
        wind_speed_kmh=weather.get("wind_speed_10m"),
        precipitation_mm=weather.get("precipitation"),
        weather_code=weather.get("weather_code"),
        aqi_us=air.get("us_aqi"),
        pm2_5=air.get("pm2_5"),
        pm10=air.get("pm10"),
        uv_index=air.get("uv_index"),
    )


def fetch_aqi_history(location: Location) -> list[dict[str, Any]]:
    """Return daily AQI from the past week, sourced from Open-Meteo's air-quality API."""
    payload = _get_json(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "past_days": 7,
            "forecast_days": 1,
            "hourly": "us_aqi",
            "timezone": "auto",
        },
    )
    hourly = payload.get("hourly", {})
    buckets: dict[str, list[float]] = {}
    for timestamp, aqi in zip(hourly.get("time", []), hourly.get("us_aqi", [])):
        if aqi is not None:
            buckets.setdefault(timestamp[:10], []).append(aqi)
    return [
        {"date": date, "aqi": round(sum(values) / len(values))}
        for date, values in sorted(buckets.items())
    ]


def fetch_day_outlook(location: Location, observed_at: str) -> list[Conditions]:
    """Fetch the next 24 hourly weather and air-quality forecasts for one location."""
    weather = _get_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
            "forecast_days": 2,
            "timezone": "auto",
        },
    ).get("hourly", {})
    air = _get_json(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "hourly": "us_aqi,pm2_5,pm10,uv_index",
            "forecast_days": 2,
            "timezone": "auto",
        },
    ).get("hourly", {})
    air_by_time = {timestamp: index for index, timestamp in enumerate(air.get("time", []))}
    outlook = []
    for index, timestamp in enumerate(weather.get("time", [])):
        if timestamp < observed_at or timestamp not in air_by_time:
            continue
        air_index = air_by_time[timestamp]
        outlook.append(Conditions(
            observed_at=timestamp,
            temperature_c=weather.get("temperature_2m", [None])[index],
            relative_humidity=weather.get("relative_humidity_2m", [None])[index],
            apparent_temperature_c=weather.get("apparent_temperature", [None])[index],
            wind_speed_kmh=weather.get("wind_speed_10m", [None])[index],
            precipitation_mm=weather.get("precipitation", [None])[index],
            weather_code=weather.get("weather_code", [None])[index],
            aqi_us=air.get("us_aqi", [None])[air_index],
            pm2_5=air.get("pm2_5", [None])[air_index],
            pm10=air.get("pm10", [None])[air_index],
            uv_index=air.get("uv_index", [None])[air_index],
        ))
        if len(outlook) == 24:
            break
    return outlook
