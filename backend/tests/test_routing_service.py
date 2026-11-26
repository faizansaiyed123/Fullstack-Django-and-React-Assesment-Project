from django.test import SimpleTestCase
from apps.routing.services import _recommend
from services.routing.checkpoint_service import sample_route

class CheckpointSamplingTests(SimpleTestCase):
    def test_samples_at_real_distance(self):
        geometry = [[0.0, 0.0], [0.1, 0.0], [0.2, 0.0]]
        points = sample_route(geometry, 10)
        self.assertAlmostEqual(points[0].distance_m, 0.0)
        self.assertGreater(points[1].distance_m, 10_000)
        self.assertAlmostEqual(points[-1].distance_m, sample_route(geometry, 10)[-1].distance_m)

class RecommendationTests(SimpleTestCase):
    def test_assignment_order(self):
        routes = [
            {"id": 0, "severe_miles": 1, "high_miles": 0, "average_risk": 1, "duration_s": 100, "recommendation_eligible": True},
            {"id": 1, "severe_miles": 0, "high_miles": 4, "average_risk": 4, "duration_s": 500, "recommendation_eligible": True},
            {"id": 2, "severe_miles": 0, "high_miles": 2, "average_risk": 3, "duration_s": 600, "recommendation_eligible": True},
        ]
        self.assertEqual(_recommend(routes), 2)
