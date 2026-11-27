from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

from services.routing.checkpoint_service import cumulative_geometry, interpolate_at_distance

class RoutingProviderError(RuntimeError):
    pass

@dataclass(frozen=True)
class RouteAlternative:
    geometry: list[list[float]]
    distance_m: float
    duration_s: float
    provider: str

def get_routes(origin, destination):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    errors = []
    routes = []

    tasks = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        if settings.ORS_API_KEY:
            tasks[executor.submit(_fetch_ors, origin, destination)] = "OpenRouteService"
        tasks[executor.submit(_fetch_osrm, origin, destination)] = "OSRM"

        for future in as_completed(tasks):
            provider_name = tasks[future]
            try:
                routes.extend(future.result())
            except Exception as exc:
                errors.append(f"{provider_name} failed: {exc}")

    routes = _deduplicate(routes)

    # If we still have fewer than 3 routes, generate distinct waypoint alternatives using OSRM
    if len(routes) < 3:
        try:
            routes.extend(
                _fetch_waypoint_alternatives(
                    origin,
                    destination,
                    needed=3 - len(routes),
                    existing_routes=routes,
                )
            )
            routes = _deduplicate(routes)
        except Exception as exc:
            errors.append(f"Waypoint alternatives failed: {exc}")

    if len(routes) < 3:
        detail = "; ".join(errors)
        message = f"Unable to generate three distinct routes (received {len(routes)})."
        if detail:
            message = f"{message} {detail}"
        raise RoutingProviderError(message)

    return routes[:3]

def _fetch_waypoint_alternatives(origin, destination, needed=2, existing_routes=None):
    alternatives = []
    seen_signatures = {
        signature
        for route in (existing_routes or [])
        if (signature := _geometry_signature(route)) is not None
    }
    mx = (origin[0] + destination[0]) / 2.0
    my = (origin[1] + destination[1]) / 2.0
    dx = destination[0] - origin[0]
    dy = destination[1] - origin[1]

    # Try perpendicular offsets (+15% and -15%)
    factors = [0.15, -0.15, 0.25, -0.25]
    for factor in factors:
        if len(alternatives) >= needed:
            break
        wp_lon = mx - dy * factor
        wp_lat = my + dx * factor
        url = (
            f"{settings.OSRM_BASE_URL.rstrip('/')}/route/v1/driving/"
            f"{origin[0]},{origin[1]};{wp_lon:.6f},{wp_lat:.6f};{destination[0]},{destination[1]}"
        )
        try:
            response = requests.get(
                url,
                params={"geometries": "geojson", "overview": "full"},
                timeout=settings.ROUTING_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            for route in data.get("routes", []):
                normalized = _normalize_route(
                    route.get("geometry", {}).get("coordinates", []),
                    {"distance": route.get("distance", 0), "duration": route.get("duration", 0)},
                    "osrm-alt",
                )
                if normalized:
                    signature = _geometry_signature(normalized)
                    if signature is not None and signature not in seen_signatures:
                        alternatives.append(normalized)
                        seen_signatures.add(signature)
                        break
        except requests.RequestException:
            continue
    return alternatives

def _fetch_ors(origin, destination):
    cache_key = _cache_key("ors", origin, destination)
    cached = cache.get(cache_key)
    if cached:
        return [RouteAlternative(**route) for route in cached]

    url = f"{settings.ORS_BASE_URL.rstrip('/')}/v2/directions/{settings.ORS_PROFILE}/geojson"
    
    # Calculate approximate distance (1 deg ~ 111km)
    dx = (origin[0] - destination[0]) * 111_000
    dy = (origin[1] - destination[1]) * 111_000
    approx_dist_m = (dx * dx + dy * dy) ** 0.5

    payload = {
        "coordinates": [[origin[0], origin[1]], [destination[0], destination[1]]],
        "instructions": False,
    }
    # Only request alternative routes if under 90,000m (ORS limit is 100,000m)
    if approx_dist_m <= 90_000:
        payload["alternative_routes"] = {"target_count": 3, "weight_factor": 1.6, "share_factor": 0.6}

    headers = {"Authorization": settings.ORS_API_KEY, "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers, timeout=settings.ROUTING_TIMEOUT_SECONDS)
    
    if response.status_code == 400 and "alternative_routes" in payload:
        payload.pop("alternative_routes", None)
        response = requests.post(url, json=payload, headers=headers, timeout=settings.ROUTING_TIMEOUT_SECONDS)

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

def _geometry_signature(route):
    try:
        cumulative = cumulative_geometry(route.geometry)
    except (IndexError, TypeError, ValueError, OverflowError):
        return None

    total_distance_m = cumulative[-1].distance_m
    if not math.isfinite(total_distance_m) or total_distance_m <= 0:
        return None

    sample_count = 21
    return tuple(
        (
            round(point.coordinate[0], 3),
            round(point.coordinate[1], 3),
        )
        for index in range(sample_count)
        for point in [
            interpolate_at_distance(
                cumulative,
                total_distance_m * index / (sample_count - 1),
            )
        ]
    )


def _deduplicate(routes):
    seen_signatures = set()
    unique = []
    for route in routes:
        signature = _geometry_signature(route)
        if signature is None or signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        unique.append(route)
    return unique

def _cache_key(provider, origin, destination):
    payload = json.dumps([provider, origin, destination], separators=(",", ":"))
    return f"route:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
