export type RiskLevel = "Low" | "Moderate" | "High" | "Severe" | "No Travel" | "Unable to verify";

export interface Weather {
  temperature_c?: number | null;
  wind_speed_mph?: number | null;
  rain_in_hr?: number | null;
  snow_in_hr?: number | null;
  forecast_time?: string;
  available?: boolean;
}

export interface Checkpoint {
  index: number;
  distance_m: number;
  distance_miles: number;
  segment_miles: number;
  lat: number;
  lon: number;
  eta: string;
  weather: Weather;
  risk: RiskLevel;
  risk_by_condition: {wind: string | null; rain: string | null; snow: string | null};
}

export interface HeatmapCoordinate {
  route_id: number;
  lat: number;
  lon: number;
}

export interface RouteOption {
  id: number;
  provider: string;
  color: string;
  distance_m: number;
  duration_s: number;
  arrival_time: string;
  geometry: [number, number][];
  checkpoints: Checkpoint[];
  heatmap_coordinates: HeatmapCoordinate[];
  risk_counts: Record<string, number>;
  severe_miles: number;
  high_miles: number;
  no_travel_miles: number;
  average_risk: number | null;
  recommendation_eligible: boolean;
  recommended: boolean;
}

export interface PlanResponse {
  origin: {label: string; lat: number; lon: number};
  destination: {label: string; lat: number; lon: number};
  departure_time: string;
  routes: RouteOption[];
  recommended_route_id: number | null;
  recommendation_note: string;
}

export interface ForecastPoint {
  route_id: number;
  lat: number;
  lon: number;
  weather: Weather;
  risk: RiskLevel;
  intensity: number | null;
}

export interface ForecastResponse {
  forecast_offset_hours: number;
  points: ForecastPoint[];
}
