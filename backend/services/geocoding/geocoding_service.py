from __future__ import annotations

import hashlib
import time

import requests
from django.conf import settings
from django.core.cache import cache

class GeocodingError(RuntimeError):
    pass

def geocode(query: str) -> dict:
    normalized = " ".join(query.split()).strip()
    if not normalized:
        raise GeocodingError("Location is required")
    cache_key = f"geocode:{hashlib.sha256(normalized.lower().encode('utf-8')).hexdigest()}"
    cached = cache.get(cache_key)
    if cached: return cached

    if settings.ORS_API_KEY:
        try:
            result = _geocode_pelias(normalized)
            if result:
                cache.set(cache_key, result, settings.GEOCODE_CACHE_TTL_SECONDS)
                return result
        except requests.RequestException:
            pass

    try:
        result = _geocode_nominatim(normalized)
    except requests.RequestException as exc:
        raise GeocodingError("Unable to geocode the location") from exc
    if not result: raise GeocodingError(f"Location not found: {normalized}")
    cache.set(cache_key, result, settings.GEOCODE_CACHE_TTL_SECONDS)
    return result

def _geocode_pelias(query):
    response = requests.get(
        settings.ORS_GEOCODING_URL,
        params={"text": query, "size": 1},
        headers={"Authorization": settings.ORS_API_KEY},
        timeout=settings.GEOCODE_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features: return None
    feature = features[0]
    coordinates = feature.get("geometry", {}).get("coordinates", [])
    if len(coordinates) < 2: return None
    return {"label": feature.get("properties", {}).get("label", query), "lat": float(coordinates[1]), "lon": float(coordinates[0])}

def _geocode_nominatim(query):
    last_request_key = "nominatim:last-request"
    last_request_at = cache.get(last_request_key)
    if last_request_at:
        elapsed = time.monotonic() - float(last_request_at)
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
    cache.set(last_request_key, time.monotonic(), 2)

    response = requests.get(
        settings.NOMINATIM_BASE_URL,
        params={"q": query, "format": "jsonv2", "limit": 1},
        headers={"User-Agent": settings.NOMINATIM_USER_AGENT},
        timeout=settings.GEOCODE_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    results = response.json()
    if not results: return None
    result = results[0]
    return {"label": result.get("display_name", query), "lat": float(result["lat"]), "lon": float(result["lon"])}
