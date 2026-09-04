import requests
import streamlit as st

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
PAST_DAYS = 7

@st.cache_data(ttl=600, show_spinner=False)
def fetch_air_quality(lat: float, lon: float):
    params = {
        "latitude": lat, "longitude": lon,
        "current": ["pm2_5", "pm10", "us_aqi", "ozone", "nitrogen_dioxide", "carbon_monoxide"],
        "hourly": ["pm2_5", "pm10", "us_aqi"],
        "past_days": PAST_DAYS, "forecast_days": 1, "timezone": "auto",
    }
    r = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()
