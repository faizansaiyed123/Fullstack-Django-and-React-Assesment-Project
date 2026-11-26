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
      <header className="page-header">
        <div>
          <p className="eyebrow">Weather-aware freight planning</p>
          <h1>Choose the safest route before the truck moves.</h1>
          <p className="lead">Three routing alternatives, ETA-aware weather checkpoints, load-sensitive risk, and a 48-hour corridor forecast.</p>
        </div>
        <div className="rule-note">Correctness first · No fabricated route or weather data</div>
      </header>

      <section className="workspace">
        <aside className="sidebar">
          <RouteForm loading={loading} onSubmit={handlePlan} />
          {error && <div className="error-box">{error}</div>}
          {plan && (
            <>
              <div className="location-summary panel">
                <div><span>From</span><strong>{plan.origin.label}</strong></div>
                <div><span>To</span><strong>{plan.destination.label}</strong></div>
              </div>
              <div className="panel route-list">
                <div className="section-head">
                  <div><p className="eyebrow">Options</p><h2>{plan.routes.length} routes returned</h2></div>
                </div>
                {plan.routes.map((route) => (
                  <RouteSummary key={route.id} route={route} selected={route.id === (selectedRoute?.id ?? null)} onSelect={() => setSelectedRouteId(route.id)} />
                ))}
              </div>
              <div className="recommendation panel">
                <p className="eyebrow">Recommendation</p>
                <p>{plan.recommendation_note}</p>
              </div>
            </>
          )}
        </aside>

        <section className="content">
          <div className="map-panel panel">
            {plan ? <RouteMap routes={plan.routes} selectedRouteId={selectedRoute?.id ?? null} forecast={forecast} /> : (
              <div className="empty-map">
                <div className="empty-map-icon">↗</div>
                <h2>Routes appear here</h2>
                <p>Enter the trip details and generate the three routing alternatives.</p>
              </div>
            )}
          </div>

          {plan && (
            <>
              <ForecastControls value={forecastOffset} loading={forecastLoading} onChange={setForecastOffset} />
              {forecastError && <div className="error-box compact">{forecastError}</div>}
              <div className="checkpoint-panel panel">
                <div className="section-head">
                  <div><p className="eyebrow">Selected route</p><h2>Checkpoint weather & ETAs</h2></div>
                  {selectedRoute && <span className="selected-route-pill">Route {selectedRoute.id + 1}</span>}
                </div>
                <div className="table-wrap">
                  <table>
                    <thead><tr><th>Mile</th><th>ETA</th><th>Risk</th><th>Wind</th><th>Rain</th><th>Snow</th></tr></thead>
                    <tbody>
                      {selectedRoute?.checkpoints.map((checkpoint) => (
                        <tr key={checkpoint.index}>
                          <td>{checkpoint.distance_miles.toFixed(1)}</td>
                          <td>{new Date(checkpoint.eta).toLocaleString()}</td>
                          <td><span className={"risk-label risk-" + checkpoint.risk.toLowerCase().replaceAll(" ", "-")}>{checkpoint.risk}</span></td>
                          <td>{checkpoint.weather.wind_speed_mph ?? "—"} mph</td>
                          <td>{checkpoint.weather.rain_in_hr ?? "—"} in/hr</td>
                          <td>{checkpoint.weather.snow_in_hr ?? "—"} in/hr</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </section>
      </section>
      <footer className="footer">Routing is provider-backed; weather values are forecast data and risk is calculated from the assessment thresholds.</footer>
    </main>
  );
}
