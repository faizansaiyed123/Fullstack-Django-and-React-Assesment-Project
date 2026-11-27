# Weather-Aware Truck Routing

A focused React + Django implementation of the Weather-Aware Truck Routing assessment. It compares three real routing alternatives using ETA-aware weather checkpoints, truck load rules, and deterministic recommendation logic.

## Assignment coverage

The app accepts origin, destination, departure date/time, load weight, and a weather sampling interval of 10, 25, or 50 miles.

It then:
1. Geocodes the endpoints.
2. Requests three distinct route alternatives from HeiGIT OpenRouteService, using OSRM as a routing fallback.
3. Samples checkpoints at true cumulative route distances.
4. Estimates truck ETA at every checkpoint from cumulative distance and route travel time.
5. Fetches hourly weather in batches from Open-Meteo, requesting wind speed in mph and preserving the documented rain/snowfall source units before conversion.
6. Applies the exact wind, rain, snow, and load thresholds from the assessment.
7. Calculates Severe, High, and No Travel mileage from checkpoint segments.
8. Recommends the eligible route using Severe miles → High miles → weighted average risk → travel time.
9. Shows all route lines, all route checkpoints, ETA, risk, and route summaries on the map.
10. Shows a corridor weather-risk heatmap controlled by a 0–48 hour forecast slider.

## Correctness and fallback policy

The application does not invent data to make a demo look healthy:
- A routing provider failure never becomes a fake straight-line route.
- The API returns exactly three geometry-distinct routes or a clear routing error; it never presents one or two routes as a complete result.
- Missing weather is shown as Unable to verify rather than Low. A known No Travel condition takes precedence over missing values in other weather variables.
- Any route with a No Travel checkpoint (including the destination checkpoint) or an unverified checkpoint remains visible but is excluded from recommendation.
- If no route is eligible, no route is recommended and recommended_route_id is null.
- Provider failures are logged server-side while the browser receives safe error messages.

## Stack

- Frontend: React, TypeScript, Vite, React Leaflet
- Backend: Django, Django REST Framework
- Routing: HeiGIT OpenRouteService, OSRM fallback
- Geocoding: HeiGIT Pelias, Nominatim fallback
- Weather: Open-Meteo
- Delivery: Docker, Docker Compose, Nginx, Gunicorn
- Quality: GitHub Actions CI

## Local setup

Backend:

    cd backend
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env
    python manage.py check
    python manage.py test
    python manage.py runserver

Put your real ORS_API_KEY in backend/.env.

Frontend:

    cd frontend
    npm ci
    copy .env.example .env
    npm run lint
    npm run build
    npm run dev

Use VITE_API_URL=http://localhost:8000/api for local development.

## Docker

Create backend/.env from backend/.env.example, set a real Django secret and routing key, then run:

    docker compose up --build

Open http://localhost:8080.

Nginx serves the React build and proxies /api/ to Django, so the browser uses one origin.

## Documentation

- docs/architecture.md
- docs/api-documentation.md
- docs/risk-calculation.md
- docs/setup-guide.md
- docs/walkthrough.md

## Security and operations

- Provider credentials stay on the server.
- Production mode requires an explicit Django secret and allowed hosts.
- Anonymous API requests are throttled.
- Route, geocode, and weather responses are cached.
- Weather requests are batched rather than executed once per checkpoint.
- Nominatim is only used as a fallback geocoder and is not used for client-side autocomplete.
