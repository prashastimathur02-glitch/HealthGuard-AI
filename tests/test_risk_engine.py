from app.risk_engine import assess_risk
from app.schemas import Conditions, UserProfile


def conditions(aqi: int) -> Conditions:
    return Conditions("2026-09-04T10:00", 30, 60, 32, 9, 0, 1, aqi, 60, 100, 4)


def test_asthmatic_outdoor_worker_has_high_risk_in_unhealthy_air():
    risk = assess_risk(UserProfile("Adult", "Asthma", "Outdoor worker"), conditions(175))
    assert risk.level == "Very high"
    assert any("N95" in action for action in risk.actions)


def test_healthy_adult_has_low_risk_in_good_air():
    risk = assess_risk(UserProfile("Adult", "None", "Indoor worker"), conditions(30))
    assert risk.level == "Low"
