import type { RouteOption, RiskLevel } from "../types";

const riskClass: Record<RiskLevel, string> = {
  Low: "risk-low", Moderate: "risk-moderate", High: "risk-high", Severe: "risk-severe",
  "No Travel": "risk-no-travel", "Unable to verify": "risk-unknown",
};

function formatDuration(seconds: number) {
  return Math.floor(seconds / 3600) + "h " + Math.round((seconds % 3600) / 60) + "m";
}

export function RouteSummary({route, selected, onSelect}: {route: RouteOption; selected: boolean; onSelect: () => void}) {
  return (
    <button className={"route-card " + (selected ? "selected" : "")} onClick={onSelect} type="button">
      <div className="route-card-top">
        <div className="route-title"><span className="route-dot" style={{background: route.color}} /><span>Route {route.id + 1}</span></div>
        {route.recommended && <span className="recommended-badge">Recommended</span>}
      </div>
      <div className="route-metrics">
        <span>{(route.distance_m / 1609.344).toFixed(0)} mi</span>
        <span>{formatDuration(route.duration_s)}</span>
        <span>{route.average_risk == null ? "—" : route.average_risk.toFixed(2)} avg risk</span>
      </div>
      <div className="risk-strip">
        {(["Severe", "High", "No Travel"] as const).map((risk) => (
          <span key={risk} className={"risk-chip " + riskClass[risk]}>
            {risk}: {risk === "Severe" ? route.severe_miles.toFixed(1) : risk === "High" ? route.high_miles.toFixed(1) : route.no_travel_miles.toFixed(1)} mi
          </span>
        ))}
      </div>
      {!route.recommendation_eligible && <p className="route-warning">Not eligible for recommendation: contains No Travel or unverified weather.</p>}
    </button>
  );
}
