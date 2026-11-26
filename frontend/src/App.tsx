import { useState } from "react";
import { MapContainer, TileLayer, Polyline, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface Checkpoint { lat:number; lon:number; eta:string; risk:string; weather:any; }
interface Route { id:number; color:string; distance_m:number; duration_s:number; arrival_time:string; geometry:[number,number][]; checkpoints:Checkpoint[]; severe_miles:number; high_miles:number; avg_risk:number; recommended:boolean; }

const riskColor: Record<string,string> = { Low:"#16a34a", Moderate:"#ca8a04", High:"#ea580c", Severe:"#dc2626", "No Travel":"#7f1d1d" };

export default function App() {
  const [origin, setOrigin] = useState("Mumbai");
  const [destination, setDestination] = useState("Pune");
  const [departure, setDeparture] = useState(new Date().toISOString().slice(0,16));
  const [load, setLoad] = useState(25000);
  const [interval, setIntervalMiles] = useState(25);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selected, setSelected] = useState<number|null>(null);
  const [slider, setSlider] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function plan() {
    setLoading(true); setError("");
    try {
      const res = await axios.post(`${API}/routing/plan-route/`, {
        origin, destination, departure_time: new Date(departure).toISOString(), load_weight_lb: load, sampling_interval_miles: interval,
      });
      setRoutes(res.data.routes);
      setSelected(res.data.recommended_route_id);
    } catch (e:any) {
      setError(e?.response?.data?.error || e.message);
    } finally { setLoading(false); }
  }

  const active = routes.find(r=>r.id===selected) || routes[0];
  const center:[number,number] = active?.geometry?.[0] ? [active.geometry[0][1], active.geometry[0][0]] : [19.07,72.87];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-6">
      <h1 className="text-2xl font-bold mb-4">Weather-Aware Truck Routing</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow p-4 space-y-3">
          <input className="w-full border rounded p-2" value={origin} onChange={e=>setOrigin(e.target.value)} placeholder="Origin"/>
          <input className="w-full border rounded p-2" value={destination} onChange={e=>setDestination(e.target.value)} placeholder="Destination"/>
          <input type="datetime-local" className="w-full border rounded p-2" value={departure} onChange={e=>setDeparture(e.target.value)}/>
          <input type="number" className="w-full border rounded p-2" value={load} onChange={e=>setLoad(+e.target.value)} placeholder="Load lb"/>
          <select className="w-full border rounded p-2" value={interval} onChange={e=>setIntervalMiles(+e.target.value)}>
            <option value={10}>Every 10 miles</option>
            <option value={25}>Every 25 miles</option>
            <option value={50}>Every 50 miles</option>
          </select>
          <button onClick={plan} disabled={loading} className="w-full bg-blue-600 text-white rounded p-2 font-semibold">{loading?"Planning...":"Plan Route"}</button>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div>
            <label className="text-sm">Forecast slider: {slider}h</label>
            <input type="range" min={0} max={48} value={slider} onChange={e=>setSlider(+e.target.value)} className="w-full"/>
          </div>
          {routes.map(r=>(
            <button key={r.id} onClick={()=>setSelected(r.id)} className={`w-full text-left border rounded p-2 ${selected===r.id?"border-blue-600":"border-slate-200"}`}>
              <div className="font-semibold">Route {r.id+1} {r.recommended && "(Recommended)"}</div>
              <div className="text-xs text-slate-600">{(r.distance_m/1609.34).toFixed(1)} mi · {(r.duration_s/3600).toFixed(1)}h · avg risk {r.avg_risk}</div>
            </button>
          ))}
        </div>
        <div className="lg:col-span-2 bg-white rounded-xl shadow overflow-hidden" style={{height:600}}>
          <MapContainer center={center} zoom={7} style={{height:"100%",width:"100%"}}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
            {routes.map(r=>(
              <Polyline key={r.id} positions={r.geometry.map(c=>[c[1],c[0]] as [number,number])} pathOptions={{color:r.color, weight:selected===r.id?5:3, opacity:selected===r.id?1:0.5}}/>
            ))}
            {active?.checkpoints.map((c,i)=>(
              <Marker key={i} position={[c.lat,c.lon]}>
                <Popup>
                  <div className="text-sm">
                    <div className="font-bold" style={{color:riskColor[c.risk]}}>{c.risk}</div>
                    <div>ETA: {new Date(c.eta).toLocaleString()}</div>
                    <div>Wind: {c.weather?.wind_speed_mph} mph</div>
                    <div>Rain: {c.weather?.rain_in_hr} in/hr</div>
                    <div>Snow: {c.weather?.snow_in_hr} in/hr</div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
