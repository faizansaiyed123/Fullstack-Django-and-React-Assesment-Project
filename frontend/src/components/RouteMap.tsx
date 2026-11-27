import { useEffect } from "react";
import { Circle, CircleMarker, MapContainer, Popup, Polyline, TileLayer, useMap } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import type { ForecastPoint, RouteOption } from "../types";

function FitBounds({ routes }: { routes: RouteOption[] }) {
  const map = useMap();
  useEffect(() => {
    const coordinates = routes.flatMap((route) => route.geometry.map(([lon, lat]) => [lat, lon] as [number, number]));
    if (coordinates.length >= 2) map.fitBounds(coordinates as LatLngBoundsExpression, { padding: [28, 28], maxZoom: 10 });
  }, [map, routes]);
  return null;
}

const riskColors: Record<string, string> = {
  Low: "#26966E",
  Moderate: "#D6A33A",
  High: "#E18B43",
  Severe: "#D65B55",
  "No Travel": "#8B303B",
  "Unable to verify": "#738394",
};

function heatRadius(routeCount: number) {
  return Math.max(3500, 6500 / Math.sqrt(Math.max(routeCount, 1)));
}

export function RouteMap({ routes, selectedRouteId, forecast }: { routes: RouteOption[]; selectedRouteId: number | null; forecast: ForecastPoint[] }) {
  const active = routes.find((route) => route.id === selectedRouteId) ?? routes[0];
  const center: [number, number] = active?.geometry[0] ? [active.geometry[0][1], active.geometry[0][0]] : [20, 77];

  return (
    <div className="map-wrap">
      <MapContainer center={center} zoom={6} scrollWheelZoom className="map">
        <TileLayer attribution="© OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <FitBounds routes={routes} />
        {routes.map((route) => (
          <Polyline
            key={"route-" + route.id}
            positions={route.geometry.map(([lon, lat]) => [lat, lon] as [number, number])}
            pathOptions={{
              color: route.color,
              weight: route.id === selectedRouteId ? 6 : 3,
              opacity: route.id === selectedRouteId ? 1 : 0.48,
            }}
          />
        ))}
        {routes.flatMap((route) =>
          route.checkpoints.map((checkpoint) => (
            <CircleMarker
              key={"checkpoint-" + route.id + "-" + checkpoint.index}
              center={[checkpoint.lat, checkpoint.lon]}
              radius={route.id === selectedRouteId ? 6 : 4}
              pathOptions={{
                color: riskColors[checkpoint.risk] ?? riskColors["Unable to verify"],
                fillColor: riskColors[checkpoint.risk] ?? riskColors["Unable to verify"],
                fillOpacity: route.id === selectedRouteId ? 0.96 : 0.44,
                weight: 1.5,
              }}
            >
              <Popup>
                <strong>Route {route.id + 1} · {checkpoint.risk}</strong>
                <div>Distance: {checkpoint.distance_miles.toFixed(1)} mi</div>
                <div>ETA: {new Date(checkpoint.eta).toLocaleString()}</div>
                <div>Wind: {checkpoint.weather.wind_speed_mph ?? "—"} mph</div>
                <div>Rain: {checkpoint.weather.rain_in_hr ?? "—"} in/hr</div>
                <div>Snow: {checkpoint.weather.snow_in_hr ?? "—"} in/hr</div>
                <div>Segment: {checkpoint.segment_miles.toFixed(1)} mi</div>
              </Popup>
            </CircleMarker>
          )),
        )}
        {forecast.map((point, index) => {
          if (point.intensity == null) return null;
          const color = riskColors[point.risk] ?? riskColors["Unable to verify"];
          return (
            <Circle
              key={"heat-" + point.route_id + "-" + point.lat + "-" + point.lon + "-" + index}
              center={[point.lat, point.lon]}
              radius={heatRadius(routes.length)}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.08 + point.intensity * 0.25, weight: 0 }}
            />
          );
        })}
      </MapContainer>

      <div className="map-legend" aria-label="Map legend">
        <div className="legend-section">
          <span className="legend-title">ROUTES</span>
          {routes.map((route) => (
            <span className="legend-item" key={"legend-route-" + route.id}>
              <i className="legend-route-line" style={{ backgroundColor: route.color }} />
              Route {route.id + 1}
            </span>
          ))}
        </div>
        <div className="legend-section legend-risk-section">
          <span className="legend-title">WEATHER RISK</span>
          {(["Low", "Moderate", "High", "Severe", "No Travel"] as const).map((risk) => (
            <span className="legend-item" key={risk}>
              <i className="legend-risk-dot" style={{ backgroundColor: riskColors[risk] }} />
              {risk}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
