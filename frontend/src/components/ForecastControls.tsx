interface ForecastControlsProps {
  value: number;
  loading: boolean;
  onChange: (value: number) => void;
}

export function ForecastControls({value, loading, onChange}: ForecastControlsProps) {
  return (
    <div className="forecast-control panel">
      <div className="forecast-control-head">
        <div><p className="eyebrow">Corridor weather</p><h2>Forecast +{value} hours</h2></div>
        <span className="muted">{loading ? "Updating…" : "Risk heatmap"}</span>
      </div>
      <input type="range" min={0} max={48} step={1} value={value} onChange={(e) => onChange(Number(e.target.value))} />
      <div className="slider-labels"><span>Departure</span><span>+24h</span><span>+48h</span></div>
    </div>
  );
}
