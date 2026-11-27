import { useEffect, useMemo, useRef, useState } from "react";
import "leaflet/dist/leaflet.css";
import { forecastCorridor, planRoute } from "./api";
import { ForecastControls } from "./components/ForecastControls";
import { RouteForm } from "./components/RouteForm";
import { RouteMap } from "./components/RouteMap";
import { RouteSummary } from "./components/RouteSummary";
import type { ForecastPoint, PlanResponse, RouteOption } from "./types";
import "./App.css";

interface PlanInput {
  origin: string;
  destination: string;
  departure_time: string;
  load_weight_lb: number;
  sampling_interval_miles: number;
}

function formatDuration(seconds: number) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);
  return hours + "h " + minutes + "m";
}

export default function App() {
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<number | null>(null);
  const [forecastOffset, setForecastOffset] = useState(0);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [error, setError] = useState("");
  const [forecastError, setForecastError] = useState("");
  const planInputRef = useRef<PlanInput | null>(null);

  const selectedRoute = useMemo<RouteOption | undefined>(
    () => plan?.routes.find((route) => route.id === selectedRouteId) ?? plan?.routes[0],
    [plan, selectedRouteId],
  );

  async function handlePlan(input: PlanInput) {
    setLoading(true);
    setError("");
    setForecastError("");
    setForecast([]);
    setForecastOffset(0);
    planInputRef.current = input;
    try {
      const result = await planRoute(input);
      setPlan(result);
      setSelectedRouteId(result.recommended_route_id ?? result.routes[0]?.id ?? null);
      await loadForecast(result, input, 0);
    } catch (requestError) {
      setPlan(null);
      setSelectedRouteId(null);
      setError(requestError instanceof Error ? requestError.message : "Unable to plan this trip.");
    } finally {
      setLoading(false);
    }
  }

  async function loadForecast(currentPlan: PlanResponse, input: PlanInput, offset: number) {
    const points = currentPlan.routes.flatMap((route) => route.heatmap_coordinates);
    if (points.length === 0) return;
    setForecastLoading(true);
    setForecastError("");
    try {
      const result = await forecastCorridor({
        departure_time: input.departure_time,
        forecast_offset_hours: offset,
        load_weight_lb: input.load_weight_lb,
        points,
      });
      setForecast(result.points);
    } catch (requestError) {
      setForecastError(requestError instanceof Error ? requestError.message : "Unable to load corridor forecast.");
    } finally {
      setForecastLoading(false);
    }
  }

  useEffect(() => {
    if (!plan || !planInputRef.current) return;
    const timer = window.setTimeout(() => {
      void loadForecast(plan, planInputRef.current as PlanInput, forecastOffset);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [forecastOffset]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="RouteWeather home">
          <img src="/routeweather-mark.svg" alt="" className="brand-mark" />
          <span>RouteWeather</span>
        </a>
        <div className="topbar-divider" />
        <div className="workspace-label">
          <span className="workspace-label-dot" />
          Route planner
        </div>
        <div className="topbar-meta">
          <span className="topbar-meta-label">WEATHER INTELLIGENCE</span>
          <span className="topbar-meta-separator" />
          <span>Wind&nbsp; · &nbsp;Rain&nbsp; · &nbsp;Snow</span>
        </div>
      </header>

      <section className="page-heading">
        <div>
          <p className="breadcrumb">WORKSPACE <span>/</span> ROUTE PLANNER</p>
          <h1>Route planner</h1>
        </div>
      </section>

      <section className="workspace">
        <aside className="sidebar">
          <RouteForm loading={loading} onSubmit={handlePlan} />

          {error && <div className="error-box" role="alert">{error}</div>}

          {plan && (
            <>
              <section className="panel route-list-panel">
                <div className="section-header">
                  <div>
                    <p className="eyebrow">ROUTE OPTIONS</p>
                    <h2>Compare routes</h2>
                  </div>
                  <span className="count-pill">{plan.routes.length} options</span>
                </div>
                <div className="routes-stack">
                  {plan.routes.map((route) => (
                    <RouteSummary
                      key={route.id}
                      route={route}
                      selected={route.id === (selectedRoute?.id ?? null)}
                      onSelect={() => setSelectedRouteId(route.id)}
                    />
                  ))}
                </div>
              </section>

              <section className="panel recommendation-panel">
                <div className="recommendation-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M5 17.5 10 12l3.2 2.8L20 7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M15.8 7H20v4.2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div className="recommendation-copy">
                  <span>ROUTE RECOMMENDATION</span>
                  <p>{plan.recommendation_note}</p>
                </div>
              </section>
            </>
          )}
        </aside>

        <section className="main-column">
          <section className="panel map-panel">
            <div className="card-header map-header">
              <div>
                <p className="eyebrow">ROUTE VISUALIZATION</p>
                <h2>Route map</h2>
              </div>
              {plan && (
                <div className="map-header-meta">
                  <span className="map-status-dot" />
                  {plan.routes.length} route alternatives
                </div>
              )}
            </div>

            {plan && selectedRoute && (
              <div className="selected-route-overview" aria-live="polite">
                <div className="selected-route-name">
                  <span className="selected-route-color" style={{ backgroundColor: selectedRoute.color }} />
                  <span>Route {selectedRoute.id + 1}</span>
                  {selectedRoute.recommended && <span className="recommended-tag">RECOMMENDED</span>}
                </div>
                <div className="overview-metric">
                  <span>DISTANCE</span>
                  <strong>{(selectedRoute.distance_m / 1609.344).toFixed(0)} <small>mi</small></strong>
                </div>
                <div className="overview-metric">
                  <span>DRIVE TIME</span>
                  <strong>{formatDuration(selectedRoute.duration_s)}</strong>
                </div>
                <div className="overview-metric">
                  <span>ARRIVAL</span>
                  <strong>{new Date(selectedRoute.arrival_time).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</strong>
                </div>
              </div>
            )}

            <div className="map-frame">
              {plan ? (
                <RouteMap routes={plan.routes} selectedRouteId={selectedRoute?.id ?? null} forecast={forecast} />
              ) : (
                <div className="empty-map">
                  <div className="empty-map-art" aria-hidden="true">
                    <svg viewBox="0 0 180 112" fill="none">
                      <path d="M10 88c29-34 40 17 69-16s44-46 91-37" stroke="#C5D8DC" strokeWidth="2" strokeDasharray="4 6" />
                      <path d="M10 88c29-34 40 17 69-16s44-46 91-37" stroke="#168C88" strokeWidth="3" strokeLinecap="round" />
                      <circle cx="10" cy="88" r="6" fill="#fff" stroke="#168C88" strokeWidth="3" />
                      <circle cx="170" cy="35" r="6" fill="#fff" stroke="#168C88" strokeWidth="3" />
                      <circle cx="79" cy="72" r="4" fill="#D9A441" stroke="#fff" strokeWidth="2" />
                      <path d="M44 22h25M56 10v25M125 84h32M141 72v24" stroke="#D4E0E6" strokeWidth="2" strokeLinecap="round" />
                      <path d="M105 11h21M115 1v20" stroke="#D4E0E6" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                  </div>
                  <h2>Your routes will appear here</h2>
                  <p>Enter your origin, destination and trip details to see route alternatives on the map.</p>
                </div>
              )}
            </div>
          </section>

          {plan && (
            <>
              <ForecastControls value={forecastOffset} loading={forecastLoading} onChange={setForecastOffset} />
              {forecastError && <div className="error-box compact" role="alert">{forecastError}</div>}

              <section className="panel checkpoint-panel">
                <div className="section-header checkpoint-header">
                  <div>
                    <p className="eyebrow">WEATHER ALONG THE ROUTE</p>
                    <h2>Checkpoint details</h2>
                    <p className="section-description">Weather conditions at the truck's estimated arrival time.</p>
                  </div>
                  {selectedRoute && (
                    <span className="selected-route-pill">
                      <span style={{ backgroundColor: selectedRoute.color }} />
                      Route {selectedRoute.id + 1}
                    </span>
                  )}
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Distance</th>
                        <th>Estimated arrival</th>
                        <th>Risk level</th>
                        <th>Wind</th>
                        <th>Rain</th>
                        <th>Snow</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedRoute?.checkpoints.map((checkpoint) => (
                        <tr key={checkpoint.index}>
                          <td className="table-distance">{checkpoint.distance_miles.toFixed(1)} mi</td>
                          <td>{new Date(checkpoint.eta).toLocaleString()}</td>
                          <td>
                            <span className={"risk-label risk-" + checkpoint.risk.toLowerCase().replaceAll(" ", "-")}>
                              {checkpoint.risk}
                            </span>
                          </td>
                          <td>{checkpoint.weather.wind_speed_mph ?? "—"} <small>mph</small></td>
                          <td>{checkpoint.weather.rain_in_hr ?? "—"} <small>in/hr</small></td>
                          <td>{checkpoint.weather.snow_in_hr ?? "—"} <small>in/hr</small></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {selectedRoute?.checkpoints.length === 0 && (
                    <p className="empty-table">No checkpoint details are available for this route.</p>
                  )}
                </div>
              </section>
            </>
          )}
        </section>
      </section>

      <footer className="footer">
        <span className="footer-brand-mark">R</span>
        <span>RouteWeather</span>
        <span className="footer-dot">·</span>
        <span>Route and weather assessments are based on provider data and the configured risk rules.</span>
      </footer>
    </main>
  );
}
