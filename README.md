# Weather-Aware Truck Routing

React + Django app helping truck drivers choose safer routes based on weather, load weight, and travel time.

## Stack
Frontend: React, TypeScript, Vite, Tailwind, Leaflet
Backend: Django, DRF
APIs: OpenRouteService (routing/geocoding), Open-Meteo (weather), Nominatim (geocoding)

## Setup
Backend:
```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```
Frontend:
```
cd frontend
npm install
copy .env.example .env
npm run dev
```

## Risk rules
Wind/Rain/Snow thresholds per assessment. Load rules applied in risk_analysis service. Recommendation prefers fewest severe miles, high miles, lowest avg risk, shortest duration.
