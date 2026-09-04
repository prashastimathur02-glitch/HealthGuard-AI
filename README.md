<<<<<<< HEAD
# HealthGuard AI

AI-powered personalized weather and AQI health advisory system.

## Problem

Generic weather and AQI alerts use the same thresholds for everyone. HealthGuard AI personalizes environmental health advisories based on the user's age group, health condition, occupation, and current environmental conditions.

## Features

- Real-time weather information
- Real-time AQI and PM2.5
- Personalized health risk score
- AI-generated health advisory
- Personalized recommendations
- 7-day alert and trend history
- What-If risk simulation

## Technology Stack

- Python
- Streamlit
- Open-Meteo API
- AQI API
- AI/LLM API
- SQLite
- Plotly

## Team

Hackathon Project — HealthGuard AI
=======
# AirAware — Personalized Weather & AQI Advisory

A hackathon MVP that uses live Open-Meteo weather and air-quality readings to create understandable guidance based on age group, health condition, and occupation.

## Highlights

- Profile-aware current risk and actions for infants, children, adults, and elderly users.
- Next-24-hour personal exposure forecast, including lower-risk outdoor time windows.
- Advisory language selector: English, Hindi, Tamil, Telugu, Bengali, and Marathi (Groq key required for translation).

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The app works without an LLM key using transparent rules. To enable Groq wording, copy `.env.example` to `.env` and add a free Groq key.

## Demo narrative

1. Search a city and show live AQI/weather values and timestamp.
2. Select `Asthma` and `Outdoor worker` to show risk and actions change.
3. Switch to a healthy indoor adult to demonstrate personalization against the same live readings.
4. Show the seven-day AQI trend and save an advisory to local history.

## Data and safety

- Live weather and AQI: Open-Meteo APIs, no API key required.
- Optional LLM: Groq, invoked only to phrase already calculated guidance.
- No user account or sensitive health data is sent anywhere by default. If Groq is configured, selected profile categories and live readings are sent in the prompt.
- Advice is informational and does not replace medical care.
>>>>>>> 02c99f6 (Add profile comparison, risk gauge, and polished UI)
