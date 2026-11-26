# Weather-Aware Truck Routing frontend

The frontend is a small React + TypeScript client for the Django API.

- src/api.ts is the typed HTTP boundary.
- src/types.ts contains the API/domain types.
- src/components/RouteForm.tsx handles trip inputs.
- src/components/RouteSummary.tsx handles route comparison.
- src/components/RouteMap.tsx handles route, checkpoint, and heatmap rendering.
- src/components/ForecastControls.tsx handles the 0–48 hour corridor forecast.
- src/App.tsx coordinates server state and user interaction.

Run npm ci, npm run lint, and npm run build before deployment.
