from django.test import SimpleTestCase
from apps.risk_analysis.services import UNKNOWN_RISK, apply_load_rules, classify_checkpoint, classify_rain, classify_snow, classify_wind

class RiskServiceTests(SimpleTestCase):
    def test_wind_boundaries(self):
        self.assertEqual(classify_wind(24.99), "Low"); self.assertEqual(classify_wind(25), "Moderate")
        self.assertEqual(classify_wind(34.99), "Moderate"); self.assertEqual(classify_wind(35), "High")
        self.assertEqual(classify_wind(44.99), "High"); self.assertEqual(classify_wind(45), "Severe")
        self.assertEqual(classify_wind(54.99), "Severe"); self.assertEqual(classify_wind(55), "No Travel")
    def test_rain_boundaries(self):
        self.assertEqual(classify_rain(.099), "Low"); self.assertEqual(classify_rain(.10), "Moderate")
        self.assertEqual(classify_rain(.249), "Moderate"); self.assertEqual(classify_rain(.25), "High")
        self.assertEqual(classify_rain(.499), "High"); self.assertEqual(classify_rain(.50), "Severe")
        self.assertEqual(classify_rain(1.0), "Severe"); self.assertEqual(classify_rain(1.001), "No Travel")
    def test_snow_boundaries(self):
        self.assertEqual(classify_snow(.499), "Low"); self.assertEqual(classify_snow(.5), "Moderate")
        self.assertEqual(classify_snow(.999), "Moderate"); self.assertEqual(classify_snow(1.0), "High")
        self.assertEqual(classify_snow(1.999), "High"); self.assertEqual(classify_snow(2.0), "Severe")
        self.assertEqual(classify_snow(3.0), "Severe"); self.assertEqual(classify_snow(3.001), "No Travel")
    def test_load_rules(self):
        self.assertEqual(apply_load_rules("Severe", 50, 35_000), "No Travel")
        self.assertEqual(apply_load_rules("High", 40, 45_000), "Severe")
        self.assertEqual(apply_load_rules("Severe", 50, 30_000), "Severe")
        self.assertEqual(apply_load_rules("Severe", 55, 1_000), "No Travel")
    def test_missing_weather_is_not_low(self):
        risk = classify_checkpoint({"wind_speed_mph": None, "rain_in_hr": 0.0, "snow_in_hr": 0.0}, 25_000)
        self.assertEqual(risk.overall, UNKNOWN_RISK)


    def test_known_no_travel_is_not_hidden_by_missing_weather(self):
        risk = classify_checkpoint(
            {"wind_speed_mph": 55, "rain_in_hr": None, "snow_in_hr": 0.0},
            25_000,
        )
        self.assertEqual(risk.wind, "No Travel")
        self.assertEqual(risk.overall, "No Travel")

    def test_incomplete_weather_without_known_no_travel_remains_unverified(self):
        risk = classify_checkpoint(
            {"wind_speed_mph": 40, "rain_in_hr": None, "snow_in_hr": 0.0},
            25_000,
        )
        self.assertEqual(risk.overall, UNKNOWN_RISK)
