
import requests
import streamlit as st

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
PAST_DAYS = 7

@st.cache_data(ttl=600, show_spinner=False)
def geocode_city(city_name: str):
    params = {"name": city_name, "count": 5, "language": "en", "format": "json"}
    r = requests.get(GEOCODE_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])

@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather(lat: float, lon: float):
    params = {
        "latitude": lat, "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "uv_index"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "uv_index", "wind_speed_10m"],
        "past_days": PAST_DAYS, "forecast_days": 1, "timezone": "auto",
    }
    r = requests.get(WEATHER_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()