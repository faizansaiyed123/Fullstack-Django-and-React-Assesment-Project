import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";

const checkpointIntervals = [
  { value: 10, label: "Every 10 miles", hint: "More frequent weather checks" },
  { value: 25, label: "Every 25 miles", hint: "Balanced checkpoint coverage" },
  { value: 50, label: "Every 50 miles", hint: "Wider spacing between checks" },
] as const;

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
  const [intervalOpen, setIntervalOpen] = useState(false);
  const [activeIntervalIndex, setActiveIntervalIndex] = useState(1);
  const intervalMenuRef = useRef<HTMLDivElement>(null);

  const selectedInterval =
    checkpointIntervals.find((option) => option.value === samplingInterval) ?? checkpointIntervals[1];

  useEffect(() => {
    if (!intervalOpen) return;

    function closeOnOutsidePointer(event: PointerEvent) {
      if (!intervalMenuRef.current?.contains(event.target as Node)) {
        setIntervalOpen(false);
      }
    }

    document.addEventListener("pointerdown", closeOnOutsidePointer);
    return () => document.removeEventListener("pointerdown", closeOnOutsidePointer);
  }, [intervalOpen]);

  function chooseInterval(value: number) {
    setSamplingInterval(value);
    setActiveIntervalIndex(checkpointIntervals.findIndex((option) => option.value === value));
    setIntervalOpen(false);
  }

  function handleIntervalKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    const selectedIndex = checkpointIntervals.findIndex((option) => option.value === samplingInterval);

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!intervalOpen) {
        setActiveIntervalIndex(selectedIndex);
        setIntervalOpen(true);
        return;
      }

      const direction = event.key === "ArrowDown" ? 1 : -1;
      setActiveIntervalIndex((current) =>
        (current + direction + checkpointIntervals.length) % checkpointIntervals.length,
      );
      return;
    }

    if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      setActiveIntervalIndex(event.key === "Home" ? 0 : checkpointIntervals.length - 1);
      setIntervalOpen(true);
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (intervalOpen) {
        chooseInterval(checkpointIntervals[activeIntervalIndex].value);
      } else {
        setActiveIntervalIndex(selectedIndex);
        setIntervalOpen(true);
      }
      return;
    }

    if (event.key === "Escape" && intervalOpen) {
      event.preventDefault();
      setIntervalOpen(false);
      return;
    }

    if (event.key === "Tab") {
      setIntervalOpen(false);
    }
  }

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
            <input type="number" min={1} max={200000} step={1} value={loadWeight} onChange={(event) => setLoadWeight(Number(event.target.value))} required />
            <span className="input-unit">LB</span>
          </span>
          <span className="field-hint">Used to evaluate load-sensitive weather risk.</span>
        </label>

        <div className="field-group checkpoint-field" ref={intervalMenuRef}>
          <span className="field-label" id="checkpoint-interval-label">Weather checkpoint interval</span>
          <button
            aria-activedescendant={
              intervalOpen ? `checkpoint-interval-option-${checkpointIntervals[activeIntervalIndex].value}` : undefined
            }
            aria-controls="checkpoint-interval-listbox"
            aria-expanded={intervalOpen}
            aria-haspopup="listbox"
            aria-labelledby="checkpoint-interval-label checkpoint-interval-value"
            className="checkpoint-select-trigger"
            id="checkpoint-interval-trigger"
            onClick={() => {
              if (intervalOpen) {
                setIntervalOpen(false);
              } else {
                setActiveIntervalIndex(checkpointIntervals.findIndex((option) => option.value === samplingInterval));
                setIntervalOpen(true);
              }
            }}
            onKeyDown={handleIntervalKeyDown}
            role="combobox"
            type="button"
          >
            <span className="checkpoint-select-current" id="checkpoint-interval-value">
              <span className="checkpoint-select-symbol" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M5 7h14M5 12h14M5 17h9" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                  <circle cx="3.5" cy="7" r="1" fill="currentColor" />
                  <circle cx="3.5" cy="12" r="1" fill="currentColor" />
                  <circle cx="3.5" cy="17" r="1" fill="currentColor" />
                </svg>
              </span>
              <span className="checkpoint-select-value">{selectedInterval.label}</span>
            </span>
            <svg className="checkpoint-select-chevron" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="m7 10 5 5 5-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          {intervalOpen && (
            <div
              className="checkpoint-select-menu"
              id="checkpoint-interval-listbox"
              role="listbox"
              aria-labelledby="checkpoint-interval-label"
            >
              {checkpointIntervals.map((option, index) => {
                const selected = option.value === samplingInterval;
                const active = index === activeIntervalIndex;

                return (
                  <div
                    aria-selected={selected}
                    className={
                      "checkpoint-select-option" +
                      (selected ? " is-selected" : "") +
                      (active ? " is-active" : "")
                    }
                    id={`checkpoint-interval-option-${option.value}`}
                    key={option.value}
                    onClick={() => chooseInterval(option.value)}
                    onMouseDown={(event) => event.preventDefault()}
                    onPointerMove={() => setActiveIntervalIndex(index)}
                    role="option"
                  >
                    <span className="checkpoint-select-option-copy">
                      <span className="checkpoint-select-option-title">{option.label}</span>
                      <span className="checkpoint-select-option-hint">{option.hint}</span>
                    </span>
                    <span className="checkpoint-select-option-check" aria-hidden="true">
                      {selected && (
                        <svg viewBox="0 0 16 16" fill="none">
                          <path d="m3.5 8 3 3 6-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      )}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          <span className="field-hint" id="checkpoint-interval-hint">
            Closer checkpoints provide more detailed coverage.
          </span>
        </div>
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
