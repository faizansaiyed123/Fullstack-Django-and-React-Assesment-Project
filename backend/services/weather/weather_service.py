from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

WEATHER_VARIABLES = "temperature_2m,wind_speed_10m,rain,snowfall"

class WeatherProviderError(RuntimeError):
    pass

def get_weather_for_points(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not points: return []
    unique = {}
    for point in points:
        lat = round(float(point["lat"]), 4); lon = round(float(point["lon"]), 4)
        when = _hour_key(_parse_datetime(point["when"]))
        unique[(lat, lon, when)] = {"lat": lat, "lon": lon, "when": point["when"]}
    unique_points = list(unique.values())
    results_by_key = {}
    for start in range(0, len(unique_points), settings.WEATHER_BATCH_SIZE):
        for weather in _fetch_batch(unique_points[start:start + settings.WEATHER_BATCH_SIZE]):
            results_by_key[(weather["lat_key"], weather["lon_key"], weather["when_key"])] = weather
    return [
        {**point, "weather": results_by_key.get(
            (round(float(point["lat"]), 4), round(float(point["lon"]), 4), _hour_key(_parse_datetime(point["when"]))),
            {"available": False},
        )}
        for point in points
    ]

def _fetch_batch(points):
    start = min(_parse_datetime(point["when"]) for point in points).replace(minute=0, second=0, microsecond=0)
    end = max(_parse_datetime(point["when"]) for point in points).replace(minute=0, second=0, microsecond=0)
    cache_key = _cache_key(points, start, end)
    cached = cache.get(cache_key)
    if cached: return cached
    response = requests.get(
        f"{settings.OPENMETEO_BASE_URL.rstrip('/')}/forecast",
        params={
            "latitude": ",".join(str(point["lat"]) for point in points),
            "longitude": ",".join(str(point["lon"]) for point in points),
            "hourly": WEATHER_VARIABLES,
            "start_hour": start.strftime("%Y-%m-%dT%H:%M"),
            "end_hour": end.strftime("%Y-%m-%dT%H:%M"),
            "timezone": "UTC",
        },
        timeout=settings.WEATHER_TIMEOUT_SECONDS,
    )
    try:
        response.raise_for_status(); payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise WeatherProviderError("Weather provider request failed") from exc
    locations = payload if isinstance(payload, list) else [payload]
    if len(locations) != len(points):
        raise WeatherProviderError("Weather provider returned an unexpected number of locations")
    normalized = []
    for location, point in zip(locations, points):
        normalized.extend(_normalize_location(location, point))
    cache.set(cache_key, normalized, settings.WEATHER_CACHE_TTL_SECONDS)
    return normalized

def _normalize_location(location, point):
    hourly = location.get("hourly", {}); times = hourly.get("time", [])
    normalized = []
    for index, timestamp in enumerate(times):
        wind = _value_at(hourly.get("wind_speed_10m"), index)
        rain_mm = _value_at(hourly.get("rain"), index)
        snow_cm = _value_at(hourly.get("snowfall"), index)
        temp = _value_at(hourly.get("temperature_2m"), index)
        normalized.append({
            "lat_key": round(float(point["lat"]), 4), "lon_key": round(float(point["lon"]), 4),
            "when_key": _hour_key(_parse_datetime(timestamp)),
            "temperature_c": temp,
            "wind_speed_mph": round(float(wind) * 2.236936, 2) if wind is not None else None,
            "rain_in_hr": round(float(rain_mm) / 25.4, 3) if rain_mm is not None else None,
            "snow_in_hr": round(float(snow_cm) / 2.54, 3) if snow_cm is not None else None,
            "forecast_time": timestamp,
            "available": all(value is not None for value in (wind, rain_mm, snow_cm)),
        })
    return normalized

def _cache_key(points, start, end):
    compact = [(round(float(point["lat"]), 4), round(float(point["lon"]), 4)) for point in points]
    raw = json.dumps([compact, start.isoformat(), end.isoformat()], separators=(",", ":"))
    return f"weather:{hashlib.sha256(raw.encode('utf-8')).hexdigest()}"

def _parse_datetime(value):
    if isinstance(value, datetime): dt = value
    else: dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def _hour_key(value):
    rounded = value.replace(minute=0, second=0, microsecond=0)
    return rounded + timedelta(hours=1) if value.minute >= 30 else rounded

def _value_at(values, index):
    try: value = values[index]
    except (IndexError, TypeError): return None
    return None if value is None else float(value)
