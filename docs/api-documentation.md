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
- exactly three distinct routes
- provider and route geometry
- distance, duration, arrival time
- true cumulative checkpoint distances
- ETA at each checkpoint
- wind, rain, snow and per-condition risk
- severe/high/no-travel mileage
- weighted average risk
- recommendation eligibility
- recommended route ID or null
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

The forecast offset is restricted to 0–48 hours. The endpoint returns each corridor point's weather and risk classification at the requested forecast time.

## Error responses

- 400: invalid input
- 422: geocoding failure
- 502: routing/provider failure
- 503: weather verification failure
- 500: unexpected server failure, with the exception logged server-side
