'''Legacy upstream implementation kept out of execution during merge resolution.
import streamlit as st
from datetime import datetime
from weather import geocode_city, fetch_weather
from aqi import fetch_air_quality
from risk_engine import build_trend_dataframe, calculate_risk_score
from ai_advisor import get_ai_advisory

st.set_page_config(page_title="Weather & AQI Health Advisory", page_icon="🌤️", layout="wide")

st.title("🌤️ AI-Powered Weather & AQI Health Advisory")
st.caption("Personalized health guidance based on live conditions and your profile — not a generic threshold alert.")

# --- Sidebar: User Profile ---
with st.sidebar:
    st.header("👤 User Profile")
    age_group = st.selectbox("Age group", ["Child", "Teen", "Adult", "Senior (60+)"])
    health_condition = st.selectbox(
        "Health condition",
        ["None", "Asthma", "Heart condition", "Allergies", "Pregnant", "Other respiratory condition"],
    )
    occupation = st.selectbox(
        "Occupation / activity type",
        ["Indoor worker", "Outdoor worker", "Student", "Athlete / frequent exerciser", "Retired / not working"],
    )
    st.divider()
    st.header("📍 Location")
    city_input = st.text_input("City name", value="Bhopal")
    search_clicked = st.button("Search location", use_container_width=True)

profile = {"age_group": age_group, "health_condition": health_condition, "occupation": occupation}

# Easy Mode for older and less technical users
with st.sidebar:
    easy_mode = st.toggle("👴 Easy Mode")
# --- Location resolution ---
if "selected_location" not in st.session_state:
    st.session_state.selected_location = None

if search_clicked or st.session_state.selected_location is None:
    if city_input:
        results = geocode_city(city_input)
        if results:
            options = {
                f"{r['name']}, {r.get('admin1', '')}, {r['country']} ({r['latitude']:.2f}, {r['longitude']:.2f})": r
                for r in results
            }
            with st.sidebar:
                choice = st.selectbox("Select match", list(options.keys()))
            st.session_state.selected_location = options[choice]
        else:
            st.warning("No matching location found. Try a different spelling.")

location = st.session_state.selected_location

if location is None:
    st.info("Enter a city name in the sidebar and click **Search location** to begin.")
    st.stop()

lat, lon = location["latitude"], location["longitude"]
st.subheader(f"📍 {location['name']}, {location.get('admin1', '')}, {location['country']}")

# --- Fetch live data ---
with st.spinner("Fetching live weather and air quality data..."):
    try:
        weather_json = fetch_weather(lat, lon)
        air_json = fetch_air_quality(lat, lon)
    except Exception as e:
        st.error(f"Failed to fetch live data: {e}")
        st.stop()

current_w = weather_json["current"]
current_a = air_json["current"]

current_conditions = {
    "temperature": current_w.get("temperature_2m"),
    "humidity": current_w.get("relative_humidity_2m"),
    "precipitation": current_w.get("precipitation"),
    "wind": current_w.get("wind_speed_10m"),
    "uv_index": current_w.get("uv_index"),
    "pm2_5": current_a.get("pm2_5"),
    "pm10": current_a.get("pm10"),
    "us_aqi": current_a.get("us_aqi"),
}

# --- Current conditions row ---
st.markdown("### Current Conditions")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Temperature", f"{current_conditions['temperature']:.1f}°C")
c2.metric("Humidity", f"{current_conditions['humidity']:.0f}%")
c3.metric("UV Index", f"{current_conditions['uv_index']:.1f}")
c4.metric("Wind", f"{current_conditions['wind']:.1f} km/h")
c5.metric("PM2.5", f"{current_conditions['pm2_5']:.1f} µg/m³")
aqi_val = current_conditions["us_aqi"]
c6.metric("US AQI", f"{aqi_val:.0f}" if aqi_val is not None else "N/A")

# --- AI Advisory ---
st.markdown("### 🩺 Your Personalized Advisory")
advisory_text = get_ai_advisory(profile, current_conditions)
st.info(advisory_text)

# --- What-If Simulator ---
st.markdown("### 🔮 What-If Simulator")

current_risk = calculate_risk_score(profile, current_conditions)

st.write(f"Current environmental risk: **{current_risk}/100**")

simulated_aqi = st.slider(
    "🌫️ Simulate AQI",
    min_value=0,
    max_value=300,
    value=int(current_conditions["us_aqi"])
    if current_conditions["us_aqi"] is not None else 100,
    step=10
)

simulated_temperature = st.slider(
    "🌡️ Simulate Temperature (°C)",
    min_value=15,
    max_value=45,
    value=int(current_conditions["temperature"]),
    step=1
)

simulated_conditions = current_conditions.copy()

simulated_conditions["us_aqi"] = simulated_aqi
simulated_conditions["temperature"] = simulated_temperature

# Calculate the new risk
simulated_risk = calculate_risk_score(
    profile,
    simulated_conditions
)

difference = simulated_risk - current_risk

st.write(f"Simulated risk: **{simulated_risk}/100**")

if difference > 0:
    st.warning(
        f"⚠️ Risk increases by **{difference} points** "
        f"if AQI becomes {simulated_aqi} and temperature becomes "
        f"{simulated_temperature}°C."
    )
elif difference < 0:
    st.success(
        f"✅ Risk decreases by **{abs(difference)} points** "
        f"under these conditions."
    )
else:
    st.info("Your risk score stays the same.")
# Easy Mode display
if easy_mode:
    st.markdown("## ❤️ Easy Mode")

    aqi = current_conditions["us_aqi"]

    if aqi is None:
        air_message = "⚠️ Air quality information is unavailable."
    elif aqi <= 50:
        air_message = "🟢 AIR IS GOOD"
    elif aqi <= 100:
        air_message = "🟡 AIR IS MODERATE"
    elif aqi <= 150:
        air_message = "🟠 AIR MAY AFFECT SENSITIVE PEOPLE"
    elif aqi <= 200:
        air_message = "🔴 AIR IS UNHEALTHY"
    elif aqi <= 300:
        air_message = "🟣 AIR IS VERY UNHEALTHY"
    else:
        air_message = "🚨 AIR IS HAZARDOUS"

    st.markdown(f"### {air_message}")

    if aqi is not None:
        st.markdown(f"### AQI: {aqi:.0f}")

    st.markdown("### 🩺 What should you do?")
    st.info(advisory_text)

    st.markdown(
        """
        ### Remember
        - Follow the simple advice above.
        - Reduce outdoor exposure when air quality is poor.
        - This information is general guidance and is not a medical diagnosis.
        """
    )
st.caption("Advisory currently uses a rule-based fallback. Add a Groq/Gemini API key in ai_advisor.py to switch to full AI-generated advice.")

# --- Trends ---
st.markdown("### 📈 7-Day Trend")
trend_df = build_trend_dataframe(weather_json, air_json)
trend_df_display = trend_df.set_index("date")

# --- 7-Day Personal Risk Forecast ---
st.markdown("### 📅 7-Day Personal Risk Forecast")

personal_risks = []

for _, row in trend_df.iterrows():
    day_conditions = {
        "temperature": row["temperature_2m"],
        "humidity": row["relative_humidity_2m"],
        "uv_index": row["uv_index"],
        "wind": row["wind_speed_10m"],
        "precipitation": row["precipitation"],
        "pm2_5": row["pm2_5"],
        "pm10": row["pm10"],
        "us_aqi": row["us_aqi"],
    }

    risk = calculate_risk_score(profile, day_conditions)
    personal_risks.append(risk)

# Create the column before displaying it
trend_df["personal_risk"] = personal_risks

st.dataframe(
    trend_df[["date", "personal_risk"]].rename(
        columns={
            "date": "Date",
            "personal_risk": "Personal Risk"
        }
    ),
    use_container_width=True,
    hide_index=True
)

highest_risk = trend_df.loc[
    trend_df["personal_risk"].idxmax()
]

st.warning(
    f"⚠️ Highest-risk day: **{highest_risk['date']}** "
    f"with a personal environmental risk of "
    f"**{int(highest_risk['personal_risk'])}/100**."
)

st.line_chart(
    trend_df.set_index("date")[["personal_risk"]]
)
tab1, tab2 = st.tabs(["Weather Trends", "AQI Trends"])
with tab1:
    st.line_chart(trend_df_display[["temperature_2m", "relative_humidity_2m"]])
    st.line_chart(trend_df_display[["uv_index", "wind_speed_10m"]])
with tab2:
    st.line_chart(trend_df_display[["pm2_5", "pm10"]])
    st.line_chart(trend_df_display[["us_aqi"]])

# --- Alert history table ---
st.markdown("### 📋 Daily Summary (Alert History)")
st.dataframe(
    trend_df_display[["temperature_2m", "us_aqi", "pm2_5"]].rename(
        columns={"temperature_2m": "Avg Temp (°C)", "us_aqi": "Avg US AQI", "pm2_5": "Avg PM2.5"}
    ).style.format("{:.1f}"),
    use_container_width=True,
)

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} — data from Open-Meteo (weather + air quality).")
st.caption("Advisory generated by Groq LLM (llama-3.1-8b-instant), personalized to your profile and live conditions.")
'''
from __future__ import annotations

import base64
from dataclasses import replace
import html
from io import BytesIO
from pathlib import Path
from textwrap import wrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from app.advisory import daily_outlook_advisory, generate_advisory, tomorrow_outlook_advisory, translate_text
from app.database import initialize, recent_advisories, save_advisory
from app.providers import DataProviderError, fetch_aqi_history, fetch_conditions, fetch_day_outlook, search_location
from app.risk_engine import aqi_band, assess_risk, risk_percentage
from app.schemas import UserProfile

load_dotenv()
st.set_page_config(page_title="AirAware", page_icon="🌤️", layout="wide")
initialize()

LANGUAGES = ["English", "Hindi", "Tamil", "Telugu", "Bengali", "Marathi"]
AGE_GROUPS = ["Infant (0–3)", "Child", "Adult", "Elderly"]
CONDITIONS = [
    "None",
    "Asthma",
    "COPD / heart condition",
    "Diabetes",
    "High blood pressure",
    "Chronic kidney disease",
    "Cancer / weak immunity",
    "Allergies",
]
OCCUPATIONS = ["Indoor worker", "Outdoor worker", "Student", "Other"]
GENDERS = ["Woman", "Man", "Non-binary / another identity", "Prefer not to say"]


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Orbitron:wght@500;600;700&family=Poppins:wght@600;700&display=swap');

        html { font-size: 19px; }
        .stApp { background: #090b10; color: #eef1f6; font-family: 'Inter', sans-serif; }
        button, input, select, textarea { font-size: 1rem !important; }
        h1 { font-family: 'Poppins', sans-serif !important; font-weight: 700 !important; font-size: calc(2.75rem + 2.5px) !important; }
        .app-tagline { margin:0 0 1.25rem; color:#aeb5c1; font-family:'Inter',sans-serif; font-size:calc(1rem + 2.5px); font-weight:600; letter-spacing:.08em; }
        h2, h3, [data-testid="stMetricLabel"] { font-family: 'Orbitron', sans-serif; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #050609 0%, #0b0d13 100%); border-right: 1px solid #353944; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: #9299a8 !important; font-family: 'Inter', sans-serif; font-size: .845rem; letter-spacing: .09em;
            text-transform: uppercase;
        }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #697181; }
        [data-testid="stSidebar"] [data-baseweb="select"] span, [data-testid="stSidebar"] input { font-size: 1.02rem !important; }

        [data-testid="stMetric"] { background: transparent; border: 1px solid #2a2e38; border-radius: 10px; padding: 16px; transition: transform .18s ease, border-color .18s ease; }
        [data-testid="stMetric"]:hover { border-color: #df3b45; transform: translateY(-3px); }
        [data-testid="stMetricLabel"] { color: #89909e !important; font-size: .62rem !important; letter-spacing: .1em; text-transform: uppercase; }
        [data-testid="stMetricValue"] { color: #f5f6f8 !important; font-weight: 700; }
        [data-testid="stMetricDelta"] { color: #aeb5c1 !important; }

        div[data-testid="stAlert"] { position: relative; z-index:1; border-left: 4px solid #df3b45 !important; background: #151b27 !important; color: #f5f7fb !important; font-family: 'Inter', sans-serif !important; font-size: 1.46rem !important; font-weight: 600 !important; line-height: 1.8 !important; }
        div[data-testid="stAlert"] p, div[data-testid="stAlert"] li, div[data-testid="stAlert"] span, div[data-testid="stAlert"] div { color: #f5f7fb !important; font-family: 'Inter', sans-serif !important; font-weight: 600 !important; line-height: 1.8 !important; }
        div[data-testid="stAlert"] strong { color: #ffffff !important; font-weight: 700 !important; }
        div[data-testid="stAlert"]::before { content: ''; position: absolute; left: -3px; top: 0; bottom: 0; width: 3px; background: #df3b45; box-shadow: -7px 0 18px rgba(223, 59, 69, .7); animation: pulse-edge 2.5s ease-in-out infinite; }
        @keyframes pulse-edge { 0%, 100% { opacity: .6; } 50% { opacity: 1; } }

        .section-header { display: flex; align-items: center; gap: .55rem; margin: 1.8rem 0 .85rem; }
        .section-header__label { font-family: 'Orbitron', sans-serif; font-size: .82rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; background: linear-gradient(90deg, #ff656d, #f4f5f7); -webkit-background-clip: text; background-clip: text; color: transparent; white-space: nowrap; }
        .section-header__line { height: 1px; flex: 1; background: linear-gradient(90deg, rgba(223, 59, 69, .9), transparent); }
        .section-header--poppins .section-header__label { font-family: 'Poppins', sans-serif; }
        .section-header--what-if .section-header__label { font-size: calc(.82rem + 8px); letter-spacing: .06em; }

        .st-key-gauge-hero { position: relative; isolation: isolate; }
        .st-key-gauge-hero::before { content: ''; position: absolute; inset: 2% 4%; z-index: -1; pointer-events: none; background: radial-gradient(circle, rgba(226, 54, 54, .15), transparent 70%); }
        .risk-moment { display:flex; align-items:center; justify-content:center; min-height:118px; margin:12px 0 4px; overflow:hidden; border-radius:12px; text-align:center; }
        .st-key-advisory-panel { position:relative; isolation:isolate; overflow:hidden; }
        .risk-moment--behind { position:absolute; inset:0; z-index:0; min-height:0; width:100%; height:100%; margin:0; border:0; border-radius:8px; opacity:.9; pointer-events:none; }
        .risk-moment--high { position:relative; color:#ffb3b8; background:radial-gradient(circle,rgba(221,47,60,.4),transparent 32%),#210b0e; border:1px solid #9c2530; }
        .risk-moment--high::before, .risk-moment--high::after { content:''; position:absolute; width:70px; height:70px; border:3px solid #ff4956; border-radius:50%; animation:alert-wave 1.5s ease-out infinite; }
        .risk-moment--high::after { animation-delay:.75s; }
        .risk-moment__alert { position:relative; z-index:1; font-family:'Poppins',sans-serif; font-size:1.02rem; font-weight:700; letter-spacing:.04em; }
        .risk-moment__burst { position:absolute; inset:0; background:conic-gradient(from 10deg,transparent 0 7%,rgba(255,80,91,.72) 7% 10%,transparent 10% 18%,rgba(255,160,70,.6) 18% 21%,transparent 21% 33%,rgba(255,80,91,.72) 33% 36%,transparent 36% 49%,rgba(255,160,70,.6) 49% 52%,transparent 52% 64%,rgba(255,80,91,.72) 64% 67%,transparent 67% 82%,rgba(255,160,70,.6) 82% 85%,transparent 85%); mask-image:radial-gradient(circle,transparent 0 17px,#000 20px,transparent 72px); opacity:0; animation:burst-flash 1.5s ease-out infinite; }
        .risk-moment__drop { position:absolute; top:19px; width:10px; height:15px; background:#d81928; border-radius:60% 40% 65% 35%; opacity:0; transform:rotate(45deg); animation:drop-fall 1.8s ease-in infinite; }
        .risk-moment__drop:nth-of-type(2) { left:19%; animation-delay:.25s; } .risk-moment__drop:nth-of-type(3) { left:31%; animation-delay:.62s; width:7px; height:11px; } .risk-moment__drop:nth-of-type(4) { left:67%; animation-delay:.12s; } .risk-moment__drop:nth-of-type(5) { left:79%; animation-delay:.46s; width:8px; height:13px; }
        .risk-moment--low { color:#d9ffe8; background:linear-gradient(180deg,#102a19,#0b1710); border:1px solid #275d3a; }
        .risk-moment__tree { display:inline-block; font-size:3.6rem; transform-origin:bottom center; animation:tree-grow 1.5s cubic-bezier(.2,.8,.2,1) both; }
        .risk-moment__low-text { margin-left:10px; font-family:'Poppins',sans-serif; font-weight:700; color:#a9efc4; }
        @keyframes alert-wave { 0% { transform:scale(.35); opacity:1; } 100% { transform:scale(2.2); opacity:0; } }
        @keyframes burst-flash { 0% { transform:scale(.2); opacity:0; } 13% { opacity:1; } 48%,100% { transform:scale(2.4); opacity:0; } }
        @keyframes drop-fall { 0% { transform:translateY(0) rotate(45deg) scale(.4); opacity:0; } 18% { opacity:1; } 100% { transform:translateY(85px) rotate(130deg) scale(1.1); opacity:0; } }
        @keyframes tree-grow { 0% { transform:scale(.15) translateY(24px); opacity:0; } 70% { transform:scale(1.12) translateY(-2px); opacity:1; } 100% { transform:scale(1) translateY(0); opacity:1; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, icon: str, poppins: bool = False, what_if: bool = False) -> None:
    extra_class = " section-header--poppins" if poppins else ""
    extra_class += " section-header--what-if" if what_if else ""
    st.markdown(
        f'<div class="section-header{extra_class}"><span class="section-header__label">{icon} {title}</span><span class="section-header__line"></span></div>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def weather_background_image(filename: str) -> str:
    """Embed the supplied local weather image so Streamlit can use it as a full background."""
    image_path = Path(__file__).with_name(filename)
    return base64.b64encode(image_path.read_bytes()).decode("ascii")


def apply_weather_background(weather_code: int | None) -> None:
    # WMO codes 0–1 are clear or mainly clear; all other weather gets the cloudy/rain scene.
    filename = "sunny.jpg" if weather_code in {0, 1} else "cloudy.jpg"
    try:
        image_data = weather_background_image(filename)
    except OSError:
        return
    st.markdown(
        f"""<style>
        .stApp {{
            background-image: linear-gradient(rgba(5, 7, 12, .38), rgba(5, 7, 12, .48)), url('data:image/jpeg;base64,{image_data}') !important;
            background-position: center center;
            background-repeat: no-repeat;
            background-size: cover;
            background-attachment: fixed;
        }}
        [data-testid="stAppViewContainer"] {{ background: transparent !important; }}
        </style>""",
        unsafe_allow_html=True,
    )


def easy_mode_message(risk_level: str) -> tuple[str, str]:
    """One simple decision for children, elders, and first-time users."""
    messages = {
        "Low": ("🟢 Today is okay", "You can follow your normal routine. Drink water and use sun protection outdoors."),
        "Moderate": ("🟡 Be a little careful", "Take breaks outdoors. Drink water and avoid very hard exercise outside."),
        "High": ("🔴 Limit outdoor time", "Stay indoors when possible. If you must go out, take short breaks and use a mask in dusty air."),
        "Very high": ("🚨 Stay safer indoors", "Postpone outdoor work or exercise when possible. Follow your doctor’s usual plan if you have breathing or heart symptoms."),
    }
    return messages[risk_level]


def advisory_icon(risk_level: str) -> str:
    return "🌳" if risk_level == "Low" else "😷"


def risk_moment(risk_level: str, behind_advisory: bool = False) -> None:
    if risk_level == "Low":
        st.markdown('<div class="risk-moment risk-moment--low" aria-label="Low risk: a tree grows"><span class="risk-moment__tree">🌳</span><span class="risk-moment__low-text">Clearer day. Enjoy it safely.</span></div>', unsafe_allow_html=True)
    elif risk_level in {"High", "Very high"}:
        placement = " risk-moment--behind" if behind_advisory else ""
        st.markdown(f'<div class="risk-moment risk-moment--high{placement}" role="alert" aria-label="High risk emergency alert"><span class="risk-moment__burst"></span><span class="risk-moment__drop"></span><span class="risk-moment__drop"></span><span class="risk-moment__drop"></span><span class="risk-moment__drop"></span><span class="risk-moment__alert">💥 HIGH RISK<br>TAKE PRECAUTIONS</span></div>', unsafe_allow_html=True)


def advisory_style(risk_level: str) -> None:
    colors = {
        "Low": ("#1e6b43", "#0f3321"),
        "Moderate": ("#c58b15", "#3b2c0a"),
        "High": ("#df3b45", "#0b0809"),
        "Very high": ("#ff4c58", "#080607"),
    }
    border, background = colors[risk_level]
    st.markdown(
        f"<style>.st-key-advisory-panel .advisory-copy {{ position:relative; z-index:1; min-height:174px; padding:22px 24px; border:1px solid {border}; border-left:5px solid {border}; border-radius:8px; background:linear-gradient(105deg,{background},#10090a); color:#fff5f5; font-family:'Inter',sans-serif; font-size:1.46rem; font-weight:600; line-height:1.8; box-shadow:inset 0 0 24px rgba(0,0,0,.28); }} .st-key-advisory-panel .advisory-copy strong {{ color:#fff; font-weight:700; }}</style>",
        unsafe_allow_html=True,
    )


def profile_picker(prefix: str, include_gender: bool = True, fixed_age: str | None = None) -> UserProfile:
    """Small reusable profile form; pregnancy is only available to eligible profiles."""
    if fixed_age:
        age = fixed_age
        st.markdown(f"**Age group:** {age}")
        st.caption("Age is matched to Profile A for a fair comparison.")
    else:
        age = st.selectbox("Age group", AGE_GROUPS, key=f"{prefix}_age")
    gender = st.selectbox("Gender", GENDERS, key=f"{prefix}_gender") if include_gender else "Prefer not to say"
    health_options = CONDITIONS.copy()
    if gender == "Woman" and age in {"Adult"}:
        health_options.append("Pregnant")
    health_key = f"{prefix}_health"
    if st.session_state.get(health_key) not in health_options:
        st.session_state[health_key] = "None"
    health = st.selectbox("Health condition", health_options, key=health_key)
    occupation = st.selectbox("Daily exposure", OCCUPATIONS, key=f"{prefix}_occupation")
    return UserProfile(age, health, occupation, gender)


def risk_gauge(score: int, level: str) -> go.Figure:
    colors = {"Low": "#1b9e77", "Moderate": "#e6ab02", "High": "#e66101", "Very high": "#d73027"}
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "/100", "font": {"size": 35}},
        title={"text": f"Spidey-sense: {level}", "font": {"size": 18}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": colors[level]},
            "steps": [
                {"range": [0, 25], "color": "#d9f0d3"},
                {"range": [25, 50], "color": "#fff7bc"},
                {"range": [50, 75], "color": "#fdd49e"},
                {"range": [75, 100], "color": "#fbb4ae"},
            ],
        },
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=60, b=10))
    return fig


def enlarge_chart_fonts(figure: go.Figure) -> go.Figure:
    """Keep charts readable from a distance during demos and presentations."""
    figure.update_layout(
        font={"family": "Inter, sans-serif", "size": 19, "color": "#eef1f6"},
        title={"font": {"family": "Poppins, sans-serif", "size": 24}},
        legend={"font": {"size": 18}},
    )
    figure.update_xaxes(title_font={"size": 20}, tickfont={"size": 17})
    figure.update_yaxes(title_font={"size": 20}, tickfont={"size": 17})
    return figure


def advisory_card(city: str, conditions, risk, advisory: str) -> bytes:
    """Create a portable, privacy-safe summary card on demand."""
    image = Image.new("RGB", (1200, 720), "#071a35")
    draw = ImageDraw.Draw(image)
    def card_font(size: int):
        # DejaVu ships with most Linux/Pillow deployments; Arial is Windows-only.
        for font_name in ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"):
            try:
                return ImageFont.truetype(font_name, size)
            except OSError:
                continue
        return ImageFont.load_default(size=size)

    title_font = card_font(46)
    body_font = card_font(28)
    small_font = card_font(22)
    accent = {"Low": "#43d17d", "Moderate": "#ffc857", "High": "#ff8c42", "Very high": "#ff5c5c"}[risk.level]
    draw.rounded_rectangle((35, 35, 1165, 685), radius=28, fill="#102b55", outline=accent, width=6)
    draw.text((80, 80), "AIR AWARE", fill="white", font=title_font)
    draw.text((80, 145), f"{city} | Personal risk: {risk.level} ({risk_percentage(risk)}/100)", fill=accent, font=body_font)
    aqi = "N/A" if conditions.aqi_us is None else str(conditions.aqi_us)
    temp = "N/A" if conditions.temperature_c is None else f"{conditions.temperature_c:.0f} C"
    draw.text((80, 205), f"Live AQI: {aqi}   |   Temperature: {temp}", fill="white", font=body_font)
    y = 285
    for line in wrap(advisory.replace("**", ""), width=70):
        draw.text((80, y), line, fill="white", font=body_font)
        y += 42
    draw.text((80, 640), "Live environmental guidance. Informational only, not medical advice.", fill="#b8c7dc", font=small_font)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


apply_theme()
st.title("AirAware")
st.markdown('<p class="app-tagline">KNOW WHEN THE AIR IS SAFE FOR YOU</p>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Your profile")
    profile = profile_picker("main")
    language = st.selectbox("Advisory language", LANGUAGES)
    easy_mode = st.toggle("Easy Mode", help="Shows only one big status and one clear action.")
    st.divider()
    st.caption("Add GROQ_API_KEY to `.env` for AI wording and translations. Safety rules always work.")

query = st.text_input("Search a city", value="Delhi", placeholder="e.g. Bengaluru, Mumbai, New York")
if not query.strip():
    st.info("Enter a city to load live conditions.")
    st.stop()
try:
    locations = search_location(query.strip())
except DataProviderError as error:
    st.error(str(error))
    st.stop()
if not locations:
    st.warning("No matching city found. Try a more specific name.")
    st.stop()
selected = st.selectbox("Location", locations, format_func=lambda item: f"{item.name}, {item.country}")
refresh = st.button("Refresh live data", type="primary")
cache_key = f"{selected.latitude:.3f},{selected.longitude:.3f},{profile},{language}"

if refresh or st.session_state.get("cache_key") != cache_key:
    try:
        with st.spinner("Fetching live weather and air-quality data..."):
            conditions = fetch_conditions(selected)
            risk = assess_risk(profile, conditions)
            advisory, source = generate_advisory(profile, conditions, risk)
            day_outlook = fetch_day_outlook(selected, conditions.observed_at)
            hourly_risks = [assess_risk(profile, item) for item in day_outlook]
            daily_advice = daily_outlook_advisory(profile, hourly_risks, day_outlook)
            tomorrow_advice = tomorrow_outlook_advisory(hourly_risks, day_outlook)
            advisory, language_status = translate_text(advisory, language)
            daily_advice, _ = translate_text(daily_advice, language)
            history = fetch_aqi_history(selected)
        st.session_state.update(
            cache_key=cache_key, conditions=conditions, risk=risk, advisory=advisory,
            source=source, language_status=language_status, history=history,
            day_outlook=day_outlook, hourly_risks=hourly_risks,
            daily_advice=daily_advice, tomorrow_advice=tomorrow_advice, scroll_to_advisory=True,
            scroll_token=st.session_state.get("scroll_token", 0) + 1,
        )
    except DataProviderError as error:
        st.error(str(error))
        st.stop()

conditions, risk, advisory = st.session_state["conditions"], st.session_state["risk"], st.session_state["advisory"]
apply_weather_background(conditions.weather_code)

if easy_mode:
    simple_heading, simple_action = easy_mode_message(risk.level)
    st.markdown("# ❤️ Easy Mode")
    st.markdown(f"## {simple_heading}")
    st.info(simple_action)
    st.markdown("### Air quality today")
    st.metric("AQI", conditions.aqi_us if conditions.aqi_us is not None else "Not available", aqi_band(conditions.aqi_us))
    st.markdown("### Your advice")
    st.info(advisory)
    st.caption("Use the sidebar to turn off Easy Mode and see the full dashboard.")
    st.stop()

section_header(f"Live conditions — {selected.name}", "◉")
st.caption(f"Updated: {conditions.observed_at} local time")
metrics = st.columns(4)
metrics[0].metric("US AQI", conditions.aqi_us if conditions.aqi_us is not None else "—", aqi_band(conditions.aqi_us))
metrics[1].metric("PM2.5", f"{conditions.pm2_5:.1f} µg/m³" if conditions.pm2_5 is not None else "—")
metrics[2].metric("Temperature", f"{conditions.temperature_c:.1f} °C" if conditions.temperature_c is not None else "—")
metrics[3].metric("Humidity", f"{conditions.relative_humidity}%" if conditions.relative_humidity is not None else "—")

st.markdown('<div id="advisory-and-risk"></div>', unsafe_allow_html=True)
left, right = st.columns([1.35, 1])
with left:
    section_header("Your advisory", advisory_icon(risk.level))
    with st.container(key="advisory-panel"):
        advisory_style(risk.level)
        if risk.level in {"High", "Very high"}:
            risk_moment(risk.level, behind_advisory=True)
        safe_advisory = html.escape(advisory).replace("**", "").replace("\n", "<br>")
        st.markdown(f'<div class="advisory-copy">{safe_advisory}</div>', unsafe_allow_html=True)
    st.caption(f"{st.session_state['source']} · {st.session_state['language_status']}")
    with st.expander("Why this advice? See the exact triggers"):
        st.markdown("**Live data and profile factors used**")
        for reason in risk.reasons:
            st.write(f"• {reason}")
        st.markdown("**Guidance triggered by those factors**")
        for action in risk.actions:
            st.write(f"• {action}")
    actions = st.columns(2)
    if actions[0].button("Save this advisory to history"):
        save_advisory(selected, profile, conditions, risk, advisory)
        st.success("Saved locally. You can revisit it below.")
    actions[1].download_button(
        "Download shareable card",
        data=advisory_card(selected.name, conditions, risk, advisory),
        file_name=f"airaware-{selected.name.lower().replace(' ', '-')}.png",
        mime="image/png",
    )
with right:
    section_header("Your personal risk", "◌")
    with st.container(key="gauge-hero"):
        st.plotly_chart(risk_gauge(risk_percentage(risk), risk.level), use_container_width=True, config={"displayModeBar": False})
    if risk.level == "Low":
        risk_moment(risk.level)
    st.caption("This combines air quality, heat, UV, health sensitivity, age, and daily exposure — not AQI alone.")

if st.session_state.pop("scroll_to_advisory", False):
    scroll_token = st.session_state.get("scroll_token", 0)
    components.html(
        f"""<script>
        const scrollToken = {scroll_token};
        window.setTimeout(() => {{
          const target = window.parent.document.getElementById('advisory-and-risk');
          if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}, 250);
        </script>""",
        height=0,
    )

section_header("WHAT IF", "↔", poppins=True, what_if=True)
st.caption("Move the bars to see how a change in air quality or temperature would affect this same person.")
simulator_left, simulator_right = st.columns(2)
current_aqi = int(conditions.aqi_us) if conditions.aqi_us is not None else 50
current_temp = int(conditions.temperature_c) if conditions.temperature_c is not None else 25
with simulator_left:
    simulated_aqi = st.slider("Air quality (AQI)", min_value=0, max_value=300, value=min(300, max(0, current_aqi)), step=5)
with simulator_right:
    simulated_temperature = st.slider("Temperature (°C)", min_value=10, max_value=50, value=min(50, max(10, current_temp)), step=1)

simulated_conditions = replace(
    conditions,
    aqi_us=simulated_aqi,
    temperature_c=float(simulated_temperature),
    apparent_temperature_c=float(simulated_temperature),
)
simulated_risk = assess_risk(profile, simulated_conditions)
current_percentage = risk_percentage(risk)
simulated_percentage = risk_percentage(simulated_risk)
result_left, result_right = st.columns([1, 2])
result_left.metric("New personal risk", f"{simulated_percentage}/100", delta=simulated_percentage - current_percentage, delta_color="inverse")
with result_right:
    if simulated_percentage > current_percentage:
        st.warning(f"Risk becomes **{simulated_risk.level.lower()}**. {simulated_risk.actions[0]}")
    elif simulated_percentage < current_percentage:
        st.success(f"Risk improves to **{simulated_risk.level.lower()}**. {simulated_risk.actions[0]}")
    else:
        st.info(f"Risk stays **{simulated_risk.level.lower()}**. {simulated_risk.actions[0]}")

section_header("Plan ahead", "↗")
st.info(st.session_state["daily_advice"])
st.success(st.session_state["tomorrow_advice"])

section_header("Compare profiles", "⇄")
with st.expander("Compare profiles — same place, same second", expanded=True):
    st.caption("This is the core idea: environmental conditions are identical, but health advice changes with the person.")
    compare_left, compare_right = st.columns(2)
    with compare_left:
        st.markdown("#### Profile A — You")
        st.markdown(f"**Age:** {profile.age_group}")
        st.markdown(f"**Gender:** {profile.gender}")
        st.markdown(f"**Health condition:** {profile.health_condition}")
        st.markdown(f"**Daily exposure:** {profile.occupation}")
        st.caption("Profile A always uses the details you entered in the sidebar.")
        profile_a = profile
    with compare_right:
        st.markdown("#### Profile B — Compare with")
        profile_b = profile_picker("compare_b", fixed_age=profile.age_group)
    if st.button("Compare these two profiles", type="primary") or "comparison" not in st.session_state:
        comparison = []
        for candidate in (profile_a, profile_b):
            candidate_risk = assess_risk(candidate, conditions)
            candidate_advisory, candidate_source = generate_advisory(candidate, conditions, candidate_risk)
            candidate_advisory, _ = translate_text(candidate_advisory, language)
            comparison.append((candidate, candidate_risk, candidate_advisory, candidate_source))
        st.session_state["comparison"] = comparison
    comparison_columns = st.columns(2)
    for column, (candidate, candidate_risk, candidate_advisory, candidate_source) in zip(comparison_columns, st.session_state["comparison"]):
        with column:
            st.markdown(f"**{candidate.age_group} · {candidate.health_condition} · {candidate.occupation}**")
            st.metric("Personal risk", f"{risk_percentage(candidate_risk)}/100", candidate_risk.level)
            st.info(candidate_advisory)
            st.caption(candidate_source)

section_header("Next 24 hours", "◷")
day_frame = pd.DataFrame([
    {"time": item.observed_at, "AQI": item.aqi_us, "Personal risk score": risk_percentage(risk_item), "Risk level": risk_item.level, "Temperature (°C)": item.temperature_c}
    for item, risk_item in zip(st.session_state["day_outlook"], st.session_state["hourly_risks"])
])
if not day_frame.empty:
    day_chart = px.line(day_frame, x="time", y=["AQI", "Personal risk score"], markers=True, title="Forecast: air quality and your personal exposure risk")
    enlarge_chart_fonts(day_chart)
    st.plotly_chart(day_chart, use_container_width=True)

section_header("AQI trend — past 7 days", "⌁")
history = pd.DataFrame(st.session_state["history"])
if not history.empty:
    history["date"] = pd.to_datetime(history["date"], errors="coerce")
    history["aqi"] = pd.to_numeric(history["aqi"], errors="coerce")
    history = history.dropna(subset=["date", "aqi"]).sort_values("date")
if not history.empty:
    precaution_days = int((history["aqi"] > 100).sum())
    st.caption(f"Precaution suggested on {precaution_days} of the last {len(history)} days (daily AQI above 100).")
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=history["date"].dt.strftime("%d %b").tolist(),
        y=history["aqi"].tolist(),
        mode="lines+markers",
        name="Daily AQI",
        line={"color": "#df3b45", "width": 3},
        marker={"size": 9, "color": "#ff737c"},
        hovertemplate="%{x}<br>AQI: %{y:.0f}<extra></extra>",
    ))
    figure.add_hline(y=100, line_dash="dash", line_color="#ffc857", annotation_text="Precaution threshold")
    figure.update_layout(
        title="Daily average AQI",
        xaxis_title="Date",
        yaxis_title="US AQI",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,8,10,.7)",
        margin=dict(l=30, r=25, t=60, b=45),
    )
    enlarge_chart_fonts(figure)
    st.plotly_chart(figure, use_container_width=True)
else:
    st.info("The AQI trend needs at least one valid historical reading.")

section_header("Alert history", "▣")
with st.expander("Your saved advisory history"):
    saved = pd.DataFrame(recent_advisories(selected.name))
    if saved.empty:
        st.caption("No saved checks for this city yet. Use ‘Save this advisory to history’ above.")
    else:
        st.dataframe(saved, use_container_width=True, hide_index=True)

st.caption("Data: Open-Meteo weather and air-quality APIs. This tool gives general information, not a diagnosis or emergency guidance.")
