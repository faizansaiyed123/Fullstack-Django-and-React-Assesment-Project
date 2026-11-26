from __future__ import annotations

import math
from dataclasses import dataclass

MILES_TO_METERS = 1609.344
EARTH_RADIUS_M = 6_371_000.0

@dataclass(frozen=True)
class RoutePoint:
    distance_m: float
    coordinate: tuple[float, float]

def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = math.radians(a[0]), math.radians(a[1])
    lon2, lat2 = math.radians(b[0]), math.radians(b[1])
    dlon = lon2 - lon1; dlat = lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))

def cumulative_geometry(geometry):
    if len(geometry) < 2: raise ValueError("Route geometry must contain at least two coordinates")
    points = [RoutePoint(0.0, (float(geometry[0][0]), float(geometry[0][1])))]
    cumulative = 0.0
    for previous, current in zip(geometry, geometry[1:]):
        a = (float(previous[0]), float(previous[1])); b = (float(current[0]), float(current[1]))
        cumulative += haversine_m(a, b)
        points.append(RoutePoint(cumulative, b))
    return points

def interpolate_at_distance(cumulative, target_m):
    if target_m <= 0: return cumulative[0]
    if target_m >= cumulative[-1].distance_m: return cumulative[-1]
    for previous, current in zip(cumulative, cumulative[1:]):
        if target_m <= current.distance_m:
            segment_m = current.distance_m - previous.distance_m
            fraction = 0.0 if segment_m <= 0 else (target_m - previous.distance_m) / segment_m
            lon = previous.coordinate[0] + (current.coordinate[0] - previous.coordinate[0]) * fraction
            lat = previous.coordinate[1] + (current.coordinate[1] - previous.coordinate[1]) * fraction
            return RoutePoint(target_m, (lon, lat))
    return cumulative[-1]

def sample_route(geometry, interval_miles):
    if interval_miles not in {10, 25, 50}: raise ValueError("Sampling interval must be 10, 25, or 50 miles")
    cumulative = cumulative_geometry(geometry)
    interval_m = interval_miles * MILES_TO_METERS
    targets = [0.0]
    target = interval_m
    total = cumulative[-1].distance_m
    while target < total:
        targets.append(target); target += interval_m
    if total > 0: targets.append(total)
    return [interpolate_at_distance(cumulative, target) for target in targets]

def sample_heatmap_points(geometry, spacing_miles=10, max_points=80):
    cumulative = cumulative_geometry(geometry)
    total = cumulative[-1].distance_m
    if total <= 0: return [list(cumulative[0].coordinate)]
    spacing_m = spacing_miles * MILES_TO_METERS
    estimated = max(2, math.ceil(total / spacing_m) + 1)
    spacing_m = total / (max_points - 1) if estimated > max_points else spacing_m
    targets = sorted(set([i * spacing_m for i in range(max_points) if i * spacing_m < total] + [total]))
    return [list(interpolate_at_distance(cumulative, target).coordinate) for target in targets]
