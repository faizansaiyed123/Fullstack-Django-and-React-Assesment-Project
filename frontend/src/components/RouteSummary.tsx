import type { RouteOption, RiskLevel } from "../types";

const riskClass: Record<RiskLevel, string> = {
  Low: "risk-low",
  Moderate: "risk-moderate",
  High: "risk-high",
  Severe: "risk-severe",
  "No Travel": "risk-no-travel",
  "Unable to verify": "risk-unknown",
};

function formatDuration(seconds: number) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);
  return hours + "h " + minutes + "m";
}

export function RouteSummary({ route, selected, onSelect }: { route: RouteOption; selected: boolean; onSelect: () => void }) {
  return (
    <button
      className={"route-card " + (selected ? "selected" : "")}
      onClick={onSelect}
      type="button"
      aria-pressed={selected}
      aria-label={"Select route " + (route.id + 1)}
    >
      <div className="route-card-heading">
        <div className="route-card-title">
          <span className="route-number" style={{ borderColor: route.color, color: route.color }}>
            {String(route.id + 1).padStart(2, "0")}
          </span>
          <span>Route {route.id + 1}</span>
        </div>
        {route.recommended && (
          <span className="recommended-badge">
            <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="m3.5 8 3 3 6-6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Recommended
          </span>
        )}
      </div>

      <div className="route-card-metrics">
        <div>
          <span>DISTANCE</span>
          <strong>{(route.distance_m / 1609.344).toFixed(0)} <small>mi</small></strong>
        </div>
        <div>
          <span>DRIVE TIME</span>
          <strong>{formatDuration(route.duration_s)}</strong>
        </div>
        <div>
          <span>AVG. RISK</span>
          <strong>{route.average_risk == null ? "—" : route.average_risk.toFixed(2)}</strong>
        </div>
      </div>

      <div className="route-exposure">
        <div className="exposure-heading">
          <span>RISK EXPOSURE</span>
          <span>{route.recommendation_eligible ? "Eligible" : "Review needed"}</span>
        </div>
        <div className="risk-strip">
          <span className={"risk-chip " + riskClass.Severe}>
            <i /> {route.severe_miles.toFixed(1)} severe mi
          </span>
          <span className={"risk-chip " + riskClass.High}>
            <i /> {route.high_miles.toFixed(1)} high mi
          </span>
          {route.no_travel_miles > 0 && (
            <span className={"risk-chip " + riskClass["No Travel"]}>
              <i /> {route.no_travel_miles.toFixed(1)} no-travel mi
            </span>
          )}
        </div>
      </div>

      {!route.recommendation_eligible && (
        <p className="route-warning">Contains No Travel or unverified weather checkpoints.</p>
      )}
    </button>
  );
}
