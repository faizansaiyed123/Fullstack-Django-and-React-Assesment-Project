import math
from datetime import datetime, timezone
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.routing.serializers import ForecastSerializer, PlanRouteSerializer
from apps.routing.services import _add_route_metrics, _recommend, plan_route
from services.routing.checkpoint_service import (
    EARTH_RADIUS_M,
    MILES_TO_METERS,
    cumulative_geometry,
    interpolate_at_distance,
    sample_route,
)
from services.routing.routing_service import (
    RouteAlternative,
    RoutingProviderError,
    _deduplicate,
    get_routes,
)


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


class CheckpointServiceTests(SimpleTestCase):
    def test_interpolates_coordinate_at_cumulative_distance(self):
        cumulative = cumulative_geometry([[0.0, 0.0], [1.0, 0.0]])
        midpoint = interpolate_at_distance(cumulative, cumulative[-1].distance_m / 2)

        self.assertAlmostEqual(midpoint.coordinate[0], 0.5, places=6)
        self.assertAlmostEqual(midpoint.coordinate[1], 0.0, places=6)
        self.assertAlmostEqual(midpoint.distance_m, cumulative[-1].distance_m / 2, places=6)

    def test_interpolation_clamps_to_route_endpoints(self):
        cumulative = cumulative_geometry([[0.0, 0.0], [1.0, 0.0]])

        self.assertEqual(interpolate_at_distance(cumulative, -1), cumulative[0])
        self.assertEqual(interpolate_at_distance(cumulative, cumulative[-1].distance_m + 1), cumulative[-1])

    def test_samples_exact_intervals_and_includes_destination_once(self):
        geometry = [[0.0, 0.0], [1.0, 0.0]]
        total_distance_m = cumulative_geometry(geometry)[-1].distance_m
        checkpoints = sample_route(geometry, 25)

        self.assertEqual(len(checkpoints), 4)
        self.assertAlmostEqual(checkpoints[0].distance_m, 0.0, places=6)
        self.assertAlmostEqual(checkpoints[1].distance_m, 25 * MILES_TO_METERS, places=6)
        self.assertAlmostEqual(checkpoints[2].distance_m, 50 * MILES_TO_METERS, places=6)
        self.assertAlmostEqual(checkpoints[-1].distance_m, total_distance_m, places=6)
        self.assertEqual(checkpoints[-1].coordinate, (1.0, 0.0))


class RoutePlanningEtaTests(SimpleTestCase):
    def test_checkpoint_eta_uses_fraction_of_route_duration(self):
        departure = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)
        route_distance_m = 30 * MILES_TO_METERS
        end_longitude = math.degrees(route_distance_m / EARTH_RADIUS_M)
        route = RouteAlternative(
            geometry=[[0.0, 0.0], [end_longitude, 0.0]],
            distance_m=route_distance_m,
            duration_s=3600,
            provider="test",
        )
        weather = {"wind_speed_mph": 10, "rain_in_hr": 0, "snow_in_hr": 0}

        with (
            patch("apps.routing.services.geocode", side_effect=[
                {"label": "Origin", "lat": 0.0, "lon": 0.0},
                {"label": "Destination", "lat": 0.0, "lon": end_longitude},
            ]),
            patch("apps.routing.services.get_routes", return_value=[route]),
            patch(
                "apps.routing.services.get_weather_for_points",
                side_effect=lambda points: [{**point, "weather": weather} for point in points],
            ) as weather_request,
        ):
            result = plan_route(
                origin_query="Origin",
                destination_query="Destination",
                departure_time=departure,
                load_weight_lb=25_000,
                sampling_interval_miles=10,
            )

        checkpoints = result["routes"][0]["checkpoints"]
        self.assertEqual(len(checkpoints), 4)
        self.assertEqual(checkpoints[0]["eta"], departure.isoformat())
        midpoint_eta = datetime.fromisoformat(checkpoints[1]["eta"])
        destination_eta = datetime.fromisoformat(checkpoints[-1]["eta"])
        self.assertAlmostEqual((midpoint_eta - departure).total_seconds(), 1200, delta=1)
        self.assertAlmostEqual((destination_eta - departure).total_seconds(), 3600, delta=1)
        self.assertEqual(weather_request.call_count, 1)


class RoutingProviderTests(SimpleTestCase):
    @staticmethod
    def make_route(geometry, distance_m=100_000, duration_s=1800, provider="test"):
        return RouteAlternative(
            geometry=geometry,
            distance_m=distance_m,
            duration_s=duration_s,
            provider=provider,
        )

    def test_deduplication_uses_geometry_not_provider_metrics(self):
        geometry = [[-100.0, 40.0], [-99.9, 40.0]]
        first = self.make_route(geometry, distance_m=100_000, duration_s=1800, provider="ors")
        duplicate = self.make_route(geometry, distance_m=100_500, duration_s=1900, provider="osrm")

        self.assertEqual(_deduplicate([first, duplicate]), [first])

    def test_route_service_returns_exactly_three_distinct_geometries(self):
        first = self.make_route([[-100.0, 40.0], [-99.9, 40.0]], provider="ors")
        first_duplicate = self.make_route(
            [[-100.0, 40.0], [-99.9, 40.0]],
            distance_m=100_500,
            duration_s=1900,
            provider="osrm",
        )
        second = self.make_route([[-100.0, 40.0], [-99.9, 40.1], [-99.9, 40.0]], provider="ors")
        third = self.make_route([[-100.0, 40.0], [-100.1, 40.1], [-99.9, 40.0]], provider="osrm")

        with (
            override_settings(ORS_API_KEY="test-key"),
            patch("services.routing.routing_service._fetch_ors", return_value=[first, second]),
            patch("services.routing.routing_service._fetch_osrm", return_value=[first_duplicate, third]),
            patch("services.routing.routing_service._fetch_waypoint_alternatives") as waypoint_fallback,
        ):
            routes = get_routes((-100.0, 40.0), (-99.9, 40.0))

        self.assertEqual(len(routes), 3)
        distinct_geometries = {tuple(tuple(point) for point in route.geometry) for route in routes}
        self.assertEqual(len(distinct_geometries), 3)
        waypoint_fallback.assert_not_called()

    def test_route_service_fails_explicitly_when_three_distinct_routes_are_unavailable(self):
        first = self.make_route([[-100.0, 40.0], [-99.9, 40.0]], provider="ors")
        second = self.make_route([[-100.0, 40.0], [-99.9, 40.1], [-99.9, 40.0]], provider="osrm")

        with (
            override_settings(ORS_API_KEY="test-key"),
            patch("services.routing.routing_service._fetch_ors", return_value=[first]),
            patch("services.routing.routing_service._fetch_osrm", return_value=[second]),
            patch("services.routing.routing_service._fetch_waypoint_alternatives", return_value=[]),
        ):
            with self.assertRaisesRegex(RoutingProviderError, "three distinct routes"):
                get_routes((-100.0, 40.0), (-99.9, 40.0))


class RouteRecommendationTests(SimpleTestCase):
    @staticmethod
    def candidate(route_id, severe_miles, high_miles, average_risk, duration_s, eligible=True):
        return {
            "id": route_id,
            "severe_miles": severe_miles,
            "high_miles": high_miles,
            "average_risk": average_risk,
            "duration_s": duration_s,
            "recommendation_eligible": eligible,
        }

    def test_recommendation_uses_assessment_lexicographic_order(self):
        routes = [
            self.candidate(0, severe_miles=1, high_miles=0, average_risk=0.0, duration_s=100),
            self.candidate(1, severe_miles=0, high_miles=2, average_risk=0.0, duration_s=100),
            self.candidate(2, severe_miles=0, high_miles=1, average_risk=0.8, duration_s=100),
            self.candidate(3, severe_miles=0, high_miles=1, average_risk=0.5, duration_s=900),
            self.candidate(4, severe_miles=0, high_miles=1, average_risk=0.5, duration_s=500),
        ]

        self.assertEqual(_recommend(routes), 4)

    def test_no_route_is_recommended_when_every_candidate_is_ineligible(self):
        routes = [
            self.candidate(0, severe_miles=0, high_miles=0, average_risk=0.0, duration_s=1, eligible=False),
            self.candidate(1, severe_miles=0, high_miles=1, average_risk=0.2, duration_s=2, eligible=False),
        ]

        self.assertIsNone(_recommend(routes))

    def test_ineligible_route_is_never_selected_over_an_eligible_route(self):
        routes = [
            self.candidate(0, severe_miles=0, high_miles=0, average_risk=0.0, duration_s=1, eligible=False),
            self.candidate(1, severe_miles=1, high_miles=0, average_risk=1.0, duration_s=100, eligible=True),
        ]

        self.assertEqual(_recommend(routes), 1)

    def test_destination_no_travel_checkpoint_disqualifies_route_without_mileage(self):
        route = {
            "checkpoints": [
                {"risk": "Low", "segment_miles": 10.0},
                {"risk": "No Travel", "segment_miles": 0.0},
            ]
        }

        _add_route_metrics(route)

        self.assertEqual(route["no_travel_miles"], 0.0)
        self.assertEqual(route["risk_counts"]["No Travel"], 1)
        self.assertFalse(route["recommendation_eligible"])
