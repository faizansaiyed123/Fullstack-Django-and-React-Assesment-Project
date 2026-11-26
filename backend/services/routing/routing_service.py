from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

class RoutingProviderError(RuntimeError):
    pass

@dataclass(frozen=True)
class RouteAlternative:
    geometry: list[list[float]]
    distance_m: float
    duration_s: float
    provider: str

def get_routes(origin, destination):
    errors = []
    routes = []
    if settings.ORS_API_KEY:
        try:
            routes.extend(_fetch_ors(origin, destination))
        except (requests.RequestException, ValueError, KeyError) as exc:
            errors.append(f"OpenRouteService failed: {exc}")

    try:
        if len(routes) < 3:
            routes.extend(_fetch_osrm(origin, destination))
    except (requests.RequestException, ValueError, KeyError) as exc:
        errors.append(f"OSRM failed: {exc}")

    routes = _deduplicate(routes)
    if len(routes) < 3:
        detail = "; ".join(errors) if errors else "providers returned fewer than three distinct routes"
        raise RoutingProviderError(f"Unable to generate 3 distinct routes. {detail}")
    return routes[:3]

def _fetch_ors(origin, destination):
    cache_key = _cache_key("ors", origin, destination)
    cached = cache.get(cache_key)
    if cached:
        return [RouteAlternative(**route) for route in cached]

    url = f"{settings.ORS_BASE_URL.rstrip('/')}/v2/directions/{settings.ORS_PROFILE}/geojson"
    response = requests.post(
        url,
        json={
            "coordinates": [[origin[0], origin[1]], [destination[0], destination[1]]],
            "alternative_routes": {"target_count": 3, "weight_factor": 1.6, "share_factor": 0.6},
            "instructions": False,
        },
        headers={"Authorization": settings.ORS_API_KEY, "Content-Type": "application/json"},
        timeout=settings.ROUTING_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    routes = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates", []) if isinstance(geometry, dict) else geometry
        summary = feature.get("properties", {}).get("summary", {})
        normalized = _normalize_route(coordinates, summary, "openrouteservice")
        if normalized:
            routes.append(normalized)
    cache.set(cache_key, [route.__dict__ for route in routes], settings.ROUTE_CACHE_TTL_SECONDS)
    return routes

def _fetch_osrm(origin, destination):
    cache_key = _cache_key("osrm", origin, destination)
    cached = cache.get(cache_key)
    if cached:
        return [RouteAlternative(**route) for route in cached]

    url = f"{settings.OSRM_BASE_URL.rstrip('/')}/route/v1/driving/{origin[0]},{origin[1]};{destination[0]},{destination[1]}"
    response = requests.get(
        url,
        params={"alternatives": "true", "geometries": "geojson", "overview": "full"},
        timeout=settings.ROUTING_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    routes = []
    for route in data.get("routes", []):
        normalized = _normalize_route(
            route.get("geometry", {}).get("coordinates", []),
            {"distance": route.get("distance", 0), "duration": route.get("duration", 0)},
            "osrm",
        )
        if normalized:
            routes.append(normalized)
    cache.set(cache_key, [route.__dict__ for route in routes], settings.ROUTE_CACHE_TTL_SECONDS)
    return routes

def _normalize_route(coordinates: Any, summary: dict[str, Any], provider: str):
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    distance_m = float(summary.get("distance", 0))
    duration_s = float(summary.get("duration", 0))
    if distance_m <= 0 or duration_s <= 0:
        return None
    geometry = [[float(point[0]), float(point[1])] for point in coordinates if len(point) >= 2]
    return RouteAlternative(geometry, distance_m, duration_s, provider) if len(geometry) >= 2 else None

def _deduplicate(routes):
    seen = set()
    unique = []
    for route in routes:
        signature = hashlib.sha256(
            json.dumps(
                {
                    "distance": round(route.distance_m, -1),
                    "duration": round(route.duration_s, -1),
                    "geometry": route.geometry[::max(1, len(route.geometry) // 20)],
                },
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        if signature not in seen:
            seen.add(signature)
            unique.append(route)
    return unique

def _cache_key(provider, origin, destination):
    payload = json.dumps([provider, origin, destination], separators=(",", ":"))
    return f"route:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
