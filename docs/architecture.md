# Architecture

The implementation keeps provider integrations and assessment rules out of the React UI.

Request flow:

    React
      |
      +-- POST /api/routing/plan-route/
      |      |
      |      +-- DRF request validation
      |      +-- geocoding service
      |      |     +-- HeiGIT Pelias
      |      |     +-- Nominatim fallback
      |      +-- routing service
      |      |     +-- HeiGIT OpenRouteService alternatives
      |      |     +-- OSRM fallback
      |      +-- checkpoint service
      |      |     +-- cumulative route distance
      |      |     +-- coordinate interpolation
      |      +-- weather service
      |      |     +-- batched Open-Meteo requests
      |      |     +-- cache
      |      +-- risk service
      |      +-- recommendation
      |
      +-- POST /api/routing/forecast/
             +-- requested 0–48h offset
             +-- batched corridor weather
             +-- risk intensity for the map overlay

Backend boundaries:

- apps/routing/views.py is a thin HTTP layer.
- apps/routing/serializers.py validates external input.
- apps/routing/services.py orchestrates the application workflow.
- services/geocoding owns provider selection and geocode caching.
- services/routing owns route providers, deduplication, and geometry sampling.
- services/weather owns weather batching, unit conversion, and caching.
- apps/risk_analysis owns every assessment-specific threshold.

Failure strategy:

The application never creates fake routes or fake weather data. A route set is usable only when three distinct routes can be produced. A checkpoint with missing weather is marked Unable to verify. Routes containing No Travel or unverified weather remain visible for transparency but cannot be recommended.

Performance strategy:

- Provider responses use Django cache.
- Weather requests are batched by multiple coordinates instead of one request per checkpoint.
- Heatmap coordinates are downsampled to a bounded number per route.
- Forecast updates are debounced on the client.
- The map uses lightweight circle overlays instead of rendering a large number of DOM markers.
