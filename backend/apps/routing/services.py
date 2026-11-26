from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from apps.risk_analysis.services import UNKNOWN_RISK, classify_checkpoint, risk_score
from services.geocoding.geocoding_service import geocode
from services.routing.checkpoint_service import MILES_TO_METERS, RoutePoint, sample_heatmap_points, sample_route
from services.routing.routing_service import RouteAlternative, get_routes
from services.weather.weather_service import get_weather_for_points

ROUTE_COLORS = ("#2563eb", "#16a34a", "#ea580c")

def plan_route(origin_query: str, destination_query: str, departure_time: datetime, load_weight_lb: float, sampling_interval_miles: int) -> dict[str, Any]:
    origin = geocode(origin_query)
    destination = geocode(destination_query)
    alternatives = get_routes((origin["lon"], origin["lat"]), (destination["lon"], destination["lat"]))

    route_payloads: list[dict[str, Any]] = []
    weather_requests: list[dict[str, Any]] = []
    checkpoint_refs: list[tuple[int, int, RoutePoint, float, float, datetime]] = []

    for route_id, route in enumerate(alternatives):
        points = sample_route(route.geometry, sampling_interval_miles)
        geometry_total_m = points[-1].distance_m
        if geometry_total_m <= 0:
            raise ValueError("Route geometry has no measurable distance")
        distance_scale = route.distance_m / geometry_total_m

        for checkpoint_index, point in enumerate(points):
            normalized_distance_m = point.distance_m * distance_scale
            fraction = point.distance_m / geometry_total_m
            eta = departure_time + timedelta(seconds=route.duration_s * fraction)
            next_distance_m = points[checkpoint_index + 1].distance_m if checkpoint_index + 1 < len(points) else point.distance_m
            segment_miles = max(0.0, (next_distance_m - point.distance_m) * distance_scale / MILES_TO_METERS)
            weather_requests.append({"lat": point.coordinate[1], "lon": point.coordinate[0], "when": eta})
            checkpoint_refs.append((route_id, checkpoint_index, point, normalized_distance_m, segment_miles, eta))

        route_payloads.append({
            "id": route_id,
            "provider": route.provider,
            "color": ROUTE_COLORS[route_id],
            "distance_m": route.distance_m,
            "duration_s": route.duration_s,
            "arrival_time": (departure_time + timedelta(seconds=route.duration_s)).isoformat(),
            "geometry": route.geometry,
            "checkpoints": [],
            "heatmap_coordinates": [
                {"route_id": route_id, "lat": point[1], "lon": point[0]}
                for point in sample_heatmap_points(route.geometry, spacing_miles=10, max_points=80)
            ],
        })

    weather_results = get_weather_for_points(weather_requests)

    for index, weather_result in enumerate(weather_results):
        route_id, checkpoint_index, point, distance_m, segment_miles, eta = checkpoint_refs[index]
        risk = classify_checkpoint(weather_result.get("weather", {}), load_weight_lb)
        route_payloads[route_id]["checkpoints"].append({
            "index": checkpoint_index,
            "distance_m": round(distance_m, 2),
            "distance_miles": round(distance_m / MILES_TO_METERS, 2),
            "segment_miles": round(segment_miles, 2),
            "lat": round(point.coordinate[1], 6),
            "lon": round(point.coordinate[0], 6),
            "eta": eta.isoformat(),
            "weather": weather_result.get("weather", {}),
            "risk": risk.overall,
            "risk_by_condition": {"wind": risk.wind, "rain": risk.rain, "snow": risk.snow},
        })

    for route in route_payloads:
        _add_route_metrics(route)

    recommended = _recommend(route_payloads)
    for route in route_payloads:
        route["recommended"] = route["id"] == recommended if recommended is not None else False

    return {
        "origin": origin,
        "destination": destination,
        "departure_time": departure_time.isoformat(),
        "routes": route_payloads,
        "recommended_route_id": recommended,
        "recommendation_note": _recommendation_note(route_payloads, recommended),
    }

def forecast_corridor(departure_time: datetime, forecast_offset_hours: int, points: list[dict[str, Any]], load_weight_lb: float) -> list[dict[str, Any]]:
    target = departure_time + timedelta(hours=forecast_offset_hours)
    weather_results = get_weather_for_points([{"lat": p["lat"], "lon": p["lon"], "when": target} for p in points])
    output = []
    for source, result in zip(points, weather_results):
        risk = classify_checkpoint(result.get("weather", {}), load_weight_lb)
        output.append({
            "route_id": source["route_id"],
            "lat": float(source["lat"]),
            "lon": float(source["lon"]),
            "weather": result.get("weather", {}),
            "risk": risk.overall,
            "intensity": _risk_intensity(risk.overall),
        })
    return output

def _add_route_metrics(route: dict[str, Any]) -> None:
    counts = {"Low": 0, "Moderate": 0, "High": 0, "Severe": 0, "No Travel": 0, UNKNOWN_RISK: 0}
    severe_miles = high_miles = no_travel_miles = weighted_score = weighted_miles = 0.0
    for checkpoint in route["checkpoints"]:
        risk = checkpoint["risk"]
        counts[risk] = counts.get(risk, 0) + 1
        miles = checkpoint["segment_miles"]
        if risk == "Severe":
            severe_miles += miles
        elif risk == "High":
            high_miles += miles
        elif risk == "No Travel":
            no_travel_miles += miles
        score = risk_score(risk)
        if score is not None and miles > 0:
            weighted_score += score * miles
            weighted_miles += miles

    route["risk_counts"] = counts
    route["severe_miles"] = round(severe_miles, 2)
    route["high_miles"] = round(high_miles, 2)
    route["no_travel_miles"] = round(no_travel_miles, 2)
    route["average_risk"] = round(weighted_score / weighted_miles, 3) if weighted_miles else None
    route["recommendation_eligible"] = no_travel_miles == 0 and counts.get(UNKNOWN_RISK, 0) == 0

def _recommend(routes: list[dict[str, Any]]) -> int | None:
    eligible = [route for route in routes if route["recommendation_eligible"]]
    if not eligible:
        return None
    return sorted(
        eligible,
        key=lambda route: (route["severe_miles"], route["high_miles"], route["average_risk"], route["duration_s"]),
    )[0]["id"]

def _recommendation_note(routes: list[dict[str, Any]], recommended: int | None) -> str:
    if recommended is None:
        return "No route can be recommended because every available route contains No Travel or unverified weather."
    route = next(route for route in routes if route["id"] == recommended)
    return f"Route {recommended + 1} has {route['severe_miles']:.1f} severe miles, {route['high_miles']:.1f} high-risk miles, average risk {route['average_risk']:.2f}, and travel time {route['duration_s'] / 3600:.1f} hours."

def _risk_intensity(risk: str) -> float | None:
    if risk == UNKNOWN_RISK:
        return None
    score = risk_score(risk)
    return 0.05 + (score / 4.0) * 0.95 if score is not None else None
