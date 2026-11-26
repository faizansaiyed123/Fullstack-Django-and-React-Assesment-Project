import requests
from django.conf import settings
from datetime import datetime, timezone, timedelta


def _get(url, params, timeout=20):
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def geocode(query):
    # Nominatim
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 5}
    headers = {"User-Agent": "weather-truck-routing/1.0"}
    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    results = []
    for d in data:
        results.append({"label": d.get("display_name"), "lat": float(d["lat"]), "lon": float(d["lon"])})
    return results


def route_alternatives(origin, destination, profile="driving-car"):
    key = settings.ORS_API_KEY
    if key:
        url = f"{settings.ORS_BASE_URL}/v2/directions/{profile}/geojson"
        body = {
            "coordinates": [[origin[1], origin[0]], [destination[1], destination[0]]],
            "alternative_routes": {"target_count": 3, "weight_factor": 1.4, "share_factor": 0.6},
            "instructions": False,
        }
        headers = {"Authorization": key, "Content-Type": "application/json"}
        r = requests.post(url, json=body, headers=headers, timeout=40)
        r.raise_for_status()
        return r.json()
    # Fallback: public OSRM (no key)
    url = "https://router.project-osrm.org/route/v1/driving/{},{};{},{}?alternatives=true&geometries=geojson&overview=full".format(origin[1], origin[0], destination[1], destination[0])
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        features = []
        for rt in data.get("routes", []):
            geom = rt.get("geometry", {})
            coords = geom.get("coordinates", []) if isinstance(geom, dict) else geom
            features.append({"properties": {"summary": {"distance": rt.get("distance", 0), "duration": rt.get("duration", 0)}}, "geometry": coords})
        return {"features": features}
    except Exception:
        # Return minimal single route as fallback
        return {"features": [{"properties": {"summary": {"distance": 0, "duration": 0}}, "geometry": [[origin[1], origin[0]], [destination[1], destination[0]]]}]}


def sample_points(geometry, interval_miles):
    # geometry: list of [lon,lat]
    import math
    pts = []
    # convert miles to meters
    interval_m = interval_miles * 1609.34
    acc = 0.0
    prev = None
    sampled = [geometry[0]]
    for coord in geometry[1:]:
        if prev is None:
            prev = coord
            continue
        # haversine
        def hav(a, b):
            R = 6371000
            la1, lo1 = math.radians(a[1]), math.radians(a[0])
            la2, lo2 = math.radians(b[1]), math.radians(b[0])
            dlat = la2 - la1
            dlon = lo2 - lo1
            h = math.sin(dlat/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dlon/2)**2
            return 2*R*math.asin(math.sqrt(h))
        d = hav(prev, coord)
        acc += d
        if acc >= interval_m:
            sampled.append(coord)
            acc = 0.0
        prev = coord
    if sampled[-1] != geometry[-1]:
        sampled.append(geometry[-1])
    return sampled


def weather_at(lat, lon, when_iso):
    # Open-Meteo forecast hourly; find nearest hour
    url = f"{settings.OPENMETEO_BASE_URL}/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,wind_speed_10m,precipitation,snowfall",
        "forecast_days": 7,
        "timezone": "UTC",
    }
    data = _get(url, params)
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    # find nearest
    best = None
    best_delta = None
    for i, t in enumerate(times):
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        target = datetime.fromisoformat(when_iso.replace("Z", "+00:00"))
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        delta = abs((dt - target).total_seconds())
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best = i
    if best is None:
        return {}
    wind_ms = hourly["wind_speed_10m"][best]
    # m/s to mph
    wind_mph = wind_ms * 2.23694 if wind_ms is not None else None
    precip_mm = hourly["precipitation"][best]  # mm per hour
    # mm/hr to in/hr
    rain_in = (precip_mm / 25.4) if precip_mm is not None else 0.0
    snow_cm = hourly["snowfall"][best]  # cm
    snow_in = (snow_cm / 2.54) if snow_cm is not None else 0.0
    return {
        "temperature_c": hourly["temperature_2m"][best],
        "wind_speed_mph": round(wind_mph, 2) if wind_mph is not None else None,
        "rain_in_hr": round(rain_in, 3),
        "snow_in_hr": round(snow_in, 3),
        "forecast_time": times[best],
        "available": True,
    }
