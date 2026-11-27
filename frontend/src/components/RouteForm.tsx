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
      origin,
      destination,
      departure_time: new Date(departureTime).toISOString(),
      load_weight_lb: loadWeight,
      sampling_interval_miles: samplingInterval,
    });
  }

  return (
    <form className="panel form-panel" onSubmit={submit}>
      <div className="form-heading">
        <div className="form-heading-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z" stroke="currentColor" strokeWidth="1.7" />
            <circle cx="12" cy="9" r="2.3" stroke="currentColor" strokeWidth="1.7" />
          </svg>
        </div>
        <div>
          <p className="eyebrow">NEW ROUTE</p>
          <h2>Trip details</h2>
        </div>
      </div>

      <div className="form-fields">
        <label className="field-group">
          <span className="field-label">Origin <span className="required-mark">*</span></span>
          <span className="input-shell">
            <span className="field-marker origin-marker" aria-hidden="true" />
            <input value={origin} onChange={(event) => setOrigin(event.target.value)} required placeholder="Enter pickup location" autoComplete="off" />
          </span>
        </label>

        <label className="field-group">
          <span className="field-label">Destination <span className="required-mark">*</span></span>
          <span className="input-shell">
            <span className="field-marker destination-marker" aria-hidden="true" />
            <input value={destination} onChange={(event) => setDestination(event.target.value)} required placeholder="Enter delivery location" autoComplete="off" />
          </span>
        </label>

        <div className="field-divider" />

        <label className="field-group">
          <span className="field-label">Departure date & time</span>
          <span className="input-shell date-input-shell">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <rect x="3.5" y="5.5" width="17" height="15" rx="2.5" stroke="currentColor" strokeWidth="1.6" />
              <path d="M7.5 3.5v4M16.5 3.5v4M3.5 10h17" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
            <input type="datetime-local" value={departureTime} onChange={(event) => setDepartureTime(event.target.value)} required />
          </span>
        </label>

        <label className="field-group">
          <span className="field-label">Truck load weight</span>
          <span className="input-shell unit-input-shell">
            <input type="number" min={0} max={200000} step={100} value={loadWeight} onChange={(event) => setLoadWeight(Number(event.target.value))} required />
            <span className="input-unit">LB</span>
          </span>
          <span className="field-hint">Used to evaluate load-sensitive weather risk.</span>
        </label>

        <label className="field-group">
          <span className="field-label">Weather checkpoint interval</span>
          <span className="input-shell select-input-shell">
            <select value={samplingInterval} onChange={(event) => setSamplingInterval(Number(event.target.value))}>
              <option value={10}>Every 10 miles</option>
              <option value={25}>Every 25 miles</option>
              <option value={50}>Every 50 miles</option>
            </select>
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="m7 10 5 5 5-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="field-hint">Closer checkpoints provide more detailed coverage.</span>
        </label>
      </div>

      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? (
          <>
            <span className="button-spinner" aria-hidden="true" />
            Planning routes…
          </>
        ) : (
          <>
            Generate routes
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M5 12h13M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </>
        )}
      </button>
      <p className="form-footnote"><span className="footnote-dot" /> Route options use live provider responses.</p>
    </form>
  );
}
