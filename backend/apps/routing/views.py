import math
from datetime import datetime, timedelta, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.weather.weather_service import route_alternatives, sample_points, weather_at, geocode
from apps.risk_analysis.services import classify_checkpoint, risk_to_score, RISK_RANK


def haversine(a, b):
    R = 6371000
    la1, lo1 = math.radians(a[0]), math.radians(a[1])
    la2, lo2 = math.radians(b[0]), math.radians(b[1])
    dlat = la2 - la1
    dlon = lo2 - lo1
    h = math.sin(dlat/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(h))


class PlanRouteView(APIView):
    def post(self, request):
        data = request.data
        origin = data.get("origin")
        destination = data.get("destination")
        departure = data.get("departure_time")
        load = float(data.get("load_weight_lb", 0))
        interval = int(data.get("sampling_interval_miles", 25))
        if not origin or not destination or not departure:
            return Response({"error": "origin, destination, departure_time required"}, status=400)
        # geocode if strings
        if isinstance(origin, str):
            res = geocode(origin)
            if not res:
                return Response({"error": "origin not found"}, status=400)
            origin = [res[0]["lat"], res[0]["lon"]]
        if isinstance(destination, str):
            res = geocode(destination)
            if not res:
                return Response({"error": "destination not found"}, status=400)
            destination = [res[0]["lat"], res[0]["lon"]]

        try:
            geojson = route_alternatives(origin, destination)
        except Exception as e:
            return Response({"error": str(e)}, status=502)

        features = geojson.get("features", [])
        routes_out = []
        for idx, f in enumerate(features):
            props = f.get("properties", {})
            summary = props.get("summary", {})
            distance_m = summary.get("distance", 0)
            duration_s = summary.get("duration", 0)
            geom_raw = f.get("geometry", [])
            if isinstance(geom_raw, dict):
                geom = geom_raw.get("coordinates", [])
            else:
                geom = geom_raw
            # sample
            pts = sample_points(geom, interval)
            # total duration per meter speed
            speed_mps = distance_m / duration_s if duration_s else 20
            dep_dt = datetime.fromisoformat(departure.replace("Z", "+00:00"))
            checkpoints = []
            # cumulative distance along geometry to estimate time
            # build cumulative distances per sampled point by matching
            # simpler: distribute by index proportion
            n = len(pts)
            for i, pt in enumerate(pts):
                # estimate fraction of distance
                # find nearest vertex index
                frac = i / max(n - 1, 1)
                eta = dep_dt + timedelta(seconds=duration_s * frac)
                weather = weather_at(pt[1], pt[0], eta.isoformat())
                risk = classify_checkpoint(weather, load)
                checkpoints.append({
                    "lat": pt[1],
                    "lon": pt[0],
                    "eta": eta.isoformat(),
                    "weather": weather,
                    "risk": risk,
                })
            # aggregate
            risk_counts = {}
            for c in checkpoints:
                risk_counts[c["risk"]] = risk_counts.get(c["risk"], 0) + 1
            severe_miles = sum(1 for c in checkpoints if c["risk"] == "Severe") * interval
            high_miles = sum(1 for c in checkpoints if c["risk"] == "High") * interval
            avg_risk = sum(risk_to_score(c["risk"]) for c in checkpoints) / max(len(checkpoints), 1)
            routes_out.append({
                "id": idx,
                "color": ["#2563eb", "#16a34a", "#ea580c"][idx % 3],
                "distance_m": distance_m,
                "duration_s": duration_s,
                "arrival_time": (dep_dt + timedelta(seconds=duration_s)).isoformat(),
                "geometry": geom,
                "checkpoints": checkpoints,
                "risk_counts": risk_counts,
                "severe_miles": severe_miles,
                "high_miles": high_miles,
                "avg_risk": round(avg_risk, 3),
            })

        # recommendation: prefer fewest severe miles, then high miles, then avg risk, then duration
        ranked = sorted(routes_out, key=lambda r: (r["severe_miles"], r["high_miles"], r["avg_risk"], r["duration_s"]))
        recommended = ranked[0]["id"] if ranked else None
        for r in routes_out:
            r["recommended"] = r["id"] == recommended

        return Response({"routes": routes_out, "recommended_route_id": recommended})
