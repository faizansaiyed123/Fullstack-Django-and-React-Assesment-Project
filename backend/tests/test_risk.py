from django.test import SimpleTestCase
from apps.risk_analysis.services import UNKNOWN_RISK, apply_load_rules, classify_checkpoint, classify_rain, classify_snow, classify_wind

class RiskServiceTests(SimpleTestCase):
    def test_wind_boundaries(self):
        self.assertEqual(classify_wind(24.99), "Low"); self.assertEqual(classify_wind(25), "Moderate")
        self.assertEqual(classify_wind(34.99), "Moderate"); self.assertEqual(classify_wind(35), "High")
        self.assertEqual(classify_wind(44.99), "High"); self.assertEqual(classify_wind(45), "Severe")
        self.assertEqual(classify_wind(54.99), "Severe"); self.assertEqual(classify_wind(55), "No Travel")
    def test_missing_weather_is_not_low(self):
        risk = classify_checkpoint({"wind_speed_mph": None, "rain_in_hr": 0.0, "snow_in_hr": 0.0}, 25_000)
        self.assertEqual(risk.overall, UNKNOWN_RISK)
    def test_load_rules(self):
        self.assertEqual(apply_load_rules("Severe", 50, 35_000), "No Travel")
        self.assertEqual(apply_load_rules("High", 40, 45_000), "Severe")
