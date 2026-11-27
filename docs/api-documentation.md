# API documentation

Base path: /api

## GET /routing/health/

Returns a simple health response for Docker/deployment checks.

Example response:

    {
      "status": "ok",
      "timestamp": "2026-11-26T10:00:00+00:00"
    }

## POST /routing/plan-route/

Request:

    {
      "origin": "Mumbai",
      "destination": "Pune",
      "departure_time": "2026-11-26T14:00:00+05:30",
      "load_weight_lb": 25000,
      "sampling_interval_miles": 25
    }

Response includes:
- normalized origin/destination
- exactly three geometry-distinct routes; if three cannot be generated, the endpoint returns HTTP 502 instead of returning a partial route set
- provider and route geometry
- distance, duration, arrival time
- true cumulative checkpoint distances
- ETA at each checkpoint
- wind, rain, snow and per-condition risk
- severe/high/no-travel mileage
- weighted average risk
- recommendation eligibility
- recommended route ID or null; it is null and all route recommended flags are false when every route contains a No Travel or unverified checkpoint
- heatmap corridor coordinates

Validation:
- load: 1–200,000 lb
- interval: 10, 25, or 50 miles
- departure: valid ISO-8601 datetime

## POST /routing/forecast/

Request:

    {
      "departure_time": "2026-11-26T14:00:00+05:30",
      "forecast_offset_hours": 24,
      "load_weight_lb": 25000,
      "points": [
        {"route_id": 0, "lat": 19.076, "lon": 72.8777}
      ]
    }

The forecast offset is restricted to 0–48 hours. The endpoint evaluates each corridor point at departure time plus the requested offset. Open-Meteo hourly values are matched to the nearest hour; this is an hourly forecast lookup, not sub-hour weather interpolation.

## Error responses

- 400: invalid input
- 422: geocoding failure
- 502: routing/provider failure, including when fewer than three distinct route alternatives can be generated
- 503: weather verification failure
- 500: unexpected server failure, with the exception logged server-side
