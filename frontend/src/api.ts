import type { ForecastResponse, HeatmapCoordinate, PlanResponse } from "./types";

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000/api").replace(/\/$/, "");

interface PlanPayload {
  origin: string;
  destination: string;
  departure_time: string;
  load_weight_lb: number;
  sampling_interval_miles: number;
}

interface ForecastPayload {
  departure_time: string;
  forecast_offset_hours: number;
  load_weight_lb: number;
  points: HeatmapCoordinate[];
}

async function requestJson<T>(path: string, options: RequestInit): Promise<T> {
  const response = await fetch(API_URL + path, {
    ...options,
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.error || "Request failed");
  return payload as T;
}

export function planRoute(payload: PlanPayload, signal?: AbortSignal) {
  return requestJson<PlanResponse>("/routing/plan-route/", {method: "POST", body: JSON.stringify(payload), signal});
}

export function forecastCorridor(payload: ForecastPayload, signal?: AbortSignal) {
  return requestJson<ForecastResponse>("/routing/forecast/", {method: "POST", body: JSON.stringify(payload), signal});
}
