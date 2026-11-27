interface ForecastControlsProps {
  value: number;
  loading: boolean;
  onChange: (value: number) => void;
}

export function ForecastControls({ value, loading, onChange }: ForecastControlsProps) {
  return (
    <section className="panel forecast-panel">
      <div className="forecast-header">
        <div className="forecast-heading">
          <div className="forecast-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M6.4 17.5h10.9a3.7 3.7 0 0 0 .2-7.4 5.5 5.5 0 0 0-10.6-1.2 4.4 4.4 0 0 0-.5 8.6Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              <path d="m9 20 1 1M14 20l1 1" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <p className="eyebrow">WEATHER CORRIDOR</p>
            <h2>Forecast timeline</h2>
          </div>
        </div>
        <div className="forecast-readout">
          <strong>+{value}h</strong>
          <span>{loading ? "Updating forecast" : value === 0 ? "At departure" : "After departure"}</span>
        </div>
      </div>
      <div className="range-wrap">
        <input
          type="range"
          min={0}
          max={48}
          step={1}
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
          aria-label="Forecast hours after departure"
        />
        <div className="slider-labels">
          <span>Departure <b>0h</b></span>
          <span>24 hours <b>24h</b></span>
          <span>48 hours <b>48h</b></span>
        </div>
      </div>
    </section>
  );
}
