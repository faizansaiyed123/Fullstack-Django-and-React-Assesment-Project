# Setup guide

## Prerequisites

- Python 3.13+
- Node.js 22+
- npm
- Git
- Docker + Docker Compose (optional)

## Environment

Create backend/.env from backend/.env.example.

Required:
- DJANGO_SECRET_KEY
- ORS_API_KEY
- ALLOWED_HOSTS
- CORS_ALLOWED_ORIGINS
- CSRF_TRUSTED_ORIGINS

Keep real provider keys only in server-side environment variables.

## Local backend

    cd backend
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env
    python manage.py check
    python manage.py test
    python manage.py runserver

## Local frontend

    cd frontend
    npm ci
    copy .env.example .env
    npm run lint
    npm run build
    npm run dev

## Docker

    copy backend/.env.example backend/.env
    docker compose up --build

Open http://localhost:8080.

The browser talks to the frontend Nginx container, which proxies /api/ requests to Django.

## Provider strategy

Primary routing/geocoding: HeiGIT OpenRouteService and Pelias.
Fallback routing: OSRM.
Fallback geocoding: Nominatim.
Weather: Open-Meteo.

The application fails safely when a provider cannot supply enough information instead of fabricating data.
