from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

RISK_LEVELS = ("Low", "Moderate", "High", "Severe", "No Travel")
RISK_RANK = {level: index for index, level in enumerate(RISK_LEVELS)}
UNKNOWN_RISK = "Unable to verify"

@dataclass(frozen=True)
class WeatherRisk:
    wind: str | None
    rain: str | None
    snow: str | None
    overall: str

def classify_wind(mph: float | None) -> str | None:
    if mph is None: return None
    if mph >= 55: return "No Travel"
    if mph >= 45: return "Severe"
    if mph >= 35: return "High"
    if mph >= 25: return "Moderate"
    return "Low"

def classify_rain(in_per_hour: float | None) -> str | None:
    if in_per_hour is None: return None
    if in_per_hour > 1.0: return "No Travel"
    if in_per_hour >= 0.5: return "Severe"
    if in_per_hour >= 0.25: return "High"
    if in_per_hour >= 0.10: return "Moderate"
    return "Low"

def classify_snow(in_per_hour: float | None) -> str | None:
    if in_per_hour is None: return None
    if in_per_hour > 3.0: return "No Travel"
    if in_per_hour >= 2.0: return "Severe"
    if in_per_hour >= 1.0: return "High"
    if in_per_hour >= 0.5: return "Moderate"
    return "Low"

def apply_load_rules(wind_risk: str | None, wind_mph: float | None, load_lb: float) -> str | None:
    if wind_mph is None: return wind_risk
    if wind_mph >= 55: return "No Travel"
    if 45 <= wind_mph < 55 and load_lb > 30_000: return "No Travel"
    if 35 <= wind_mph < 45 and load_lb > 40_000: return "Severe"
    return wind_risk

def combine_risks(risks: list[str | None]) -> str:
    if any(risk is None for risk in risks):
        return UNKNOWN_RISK
    return max((risk for risk in risks if risk is not None), key=RISK_RANK.__getitem__)

def classify_checkpoint(weather: Mapping[str, float | int | None], load_lb: float) -> WeatherRisk:
    wind_speed = _as_float(weather.get("wind_speed_mph"))
    wind = apply_load_rules(classify_wind(wind_speed), wind_speed, load_lb)
    rain = classify_rain(_as_float(weather.get("rain_in_hr")))
    snow = classify_snow(_as_float(weather.get("snow_in_hr")))
    return WeatherRisk(wind=wind, rain=rain, snow=snow, overall=combine_risks([wind, rain, snow]))

def risk_score(level: str) -> int | None:
    return RISK_RANK.get(level)

def _as_float(value: float | int | None) -> float | None:
    return None if value is None else float(value)
