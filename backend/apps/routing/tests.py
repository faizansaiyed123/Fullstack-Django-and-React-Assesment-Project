from django.test import SimpleTestCase
from apps.routing.serializers import ForecastSerializer, PlanRouteSerializer

class RoutingSerializerTests(SimpleTestCase):
    def test_interval_is_restricted(self):
        serializer = PlanRouteSerializer(data={
            "origin": "Mumbai", "destination": "Pune", "departure_time": "2026-11-26T12:00:00Z",
            "load_weight_lb": 25000, "sampling_interval_miles": 15,
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("sampling_interval_miles", serializer.errors)

    def test_forecast_offsets_are_restricted(self):
        serializer = ForecastSerializer(data={
            "departure_time": "2026-11-26T12:00:00Z", "forecast_offset_hours": 49,
            "load_weight_lb": 25000, "points": [{"route_id": 0, "lat": 19.0, "lon": 73.0}],
        })
        self.assertFalse(serializer.is_valid())
