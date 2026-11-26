from django.test import SimpleTestCase
from apps.risk_analysis.services import classify_wind_clean, classify_rain, classify_snow, apply_load_rules


class RiskTests(SimpleTestCase):
    def test_wind_boundaries(self):
        self.assertEqual(classify_wind_clean(24), "Low")
        self.assertEqual(classify_wind_clean(25), "Moderate")
        self.assertEqual(classify_wind_clean(35), "High")
        self.assertEqual(classify_wind_clean(45), "Severe")
        self.assertEqual(classify_wind_clean(55), "No Travel")

    def test_rain(self):
        self.assertEqual(classify_rain(0.05), "Low")
        self.assertEqual(classify_rain(0.10), "Moderate")
        self.assertEqual(classify_rain(0.30), "High")
        self.assertEqual(classify_rain(0.60), "Severe")
        self.assertEqual(classify_rain(1.10), "No Travel")

    def test_snow(self):
        self.assertEqual(classify_snow(0.4), "Low")
        self.assertEqual(classify_snow(0.5), "Moderate")
        self.assertEqual(classify_snow(1.5), "High")
        self.assertEqual(classify_snow(2.5), "Severe")
        self.assertEqual(classify_snow(3.1), "No Travel")

    def test_load_rules(self):
        self.assertEqual(apply_load_rules("Severe", 50, 35000), "No Travel")
        self.assertEqual(apply_load_rules("High", 40, 45000), "Severe")
