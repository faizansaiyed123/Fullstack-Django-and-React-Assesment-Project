import { useState } from "react";
import type { FormEvent } from "react";

interface RouteFormProps {
  loading: boolean;
  onSubmit: (payload: {
    origin: string;
    destination: string;
    departure_time: string;
    load_weight_lb: number;
    sampling_interval_miles: number;
  }) => void;
}

export function RouteForm({ loading, onSubmit }: RouteFormProps) {
  const [origin, setOrigin] = useState("Mumbai");
  const [destination, setDestination] = useState("Pune");
  const [departureTime, setDepartureTime] = useState(() => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
  });
  const [loadWeight, setLoadWeight] = useState(25_000);
  const [samplingInterval, setSamplingInterval] = useState(25);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit({
      origin, destination, departure_time: new Date(departureTime).toISOString(),
      load_weight_lb: loadWeight, sampling_interval_miles: samplingInterval,
    });
  }

  return (
    <form className="panel form-panel" onSubmit={submit}>
      <div><p className="eyebrow">Trip inputs</p><h2>Plan a safer truck route</h2><p className="muted">Weather is evaluated at the truck's estimated arrival time for every checkpoint.</p></div>
      <label><span>Origin</span><input value={origin} onChange={(e) => setOrigin(e.target.value)} required placeholder="City or address" /></label>
      <label><span>Destination</span><input value={destination} onChange={(e) => setDestination(e.target.value)} required placeholder="City or address" /></label>
      <label><span>Departure</span><input type="datetime-local" value={departureTime} onChange={(e) => setDepartureTime(e.target.value)} required /></label>
      <label><span>Load weight (lb)</span><input type="number" min={0} max={200000} step={100} value={loadWeight} onChange={(e) => setLoadWeight(Number(e.target.value))} required /></label>
      <label><span>Weather checkpoint interval</span><select value={samplingInterval} onChange={(e) => setSamplingInterval(Number(e.target.value))}><option value={10}>Every 10 miles</option><option value={25}>Every 25 miles</option><option value={50}>Every 50 miles</option></select></label>
      <button className="primary-button" type="submit" disabled={loading}>{loading ? "Planning…" : "Generate 3 routes"}</button>
    </form>
  );
}
