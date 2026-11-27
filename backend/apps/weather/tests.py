from unittest.mock import Mock, patch

import requests

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from services.weather.weather_service import WeatherProviderError, get_weather_for_points


class WeatherServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _weather_response(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "hourly": {
                "time": ["2026-11-27T12:00"],
                "temperature_2m": [20],
                "wind_speed_10m": [10],
                "rain": [0],
                "snowfall": [0],
            }
        }
        return response

    @override_settings(WEATHER_CACHE_TTL_SECONDS=900, WEATHER_BATCH_SIZE=50)
    @patch("services.weather.weather_service.requests.get")
    def test_repeated_request_reuses_fifteen_minute_cache(self, mock_get):
        mock_get.return_value = self._weather_response()
        points = [{"lat": 19.0760, "lon": 72.8777, "when": "2026-11-27T12:00:00Z"}]

        first_result = get_weather_for_points(points)
        second_result = get_weather_for_points(points)

        self.assertEqual(first_result, second_result)
        self.assertEqual(mock_get.call_count, 1)
        self.assertTrue(first_result[0]["weather"]["available"])

    @override_settings(
        WEATHER_MAX_RETRIES=2,
        WEATHER_RETRY_BACKOFF_SECONDS=0.5,
        WEATHER_MAX_RETRY_DELAY_SECONDS=10,
        WEATHER_CACHE_TTL_SECONDS=900,
    )
    @patch("services.weather.weather_service.time.sleep")
    @patch("services.weather.weather_service.requests.get")
    def test_retries_rate_limit_using_retry_after_header(self, mock_get, mock_sleep):
        throttled = Mock()
        throttled.status_code = 429
        throttled.headers = {"Retry-After": "2"}
        success = self._weather_response()
        mock_get.side_effect = [throttled, success]

        result = get_weather_for_points([
            {"lat": 19.0760, "lon": 72.8777, "when": "2026-11-27T12:00:00Z"}
        ])

        self.assertTrue(result[0]["weather"]["available"])
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(2.0)

    @override_settings(
        WEATHER_MAX_RETRIES=2,
        WEATHER_RETRY_BACKOFF_SECONDS=0.5,
        WEATHER_MAX_RETRY_DELAY_SECONDS=10,
    )
    @patch("services.weather.weather_service.time.sleep")
    @patch("services.weather.weather_service.requests.get")
    def test_uses_bounded_exponential_backoff_after_connection_errors(self, mock_get, mock_sleep):
        mock_get.side_effect = [
            requests.ConnectionError("temporary network failure"),
            requests.ConnectionError("temporary network failure"),
            requests.ConnectionError("temporary network failure"),
        ]

        with self.assertRaises(WeatherProviderError):
            get_weather_for_points([
                {"lat": 19.0760, "lon": 72.8777, "when": "2026-11-27T12:00:00Z"}
            ])

        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual([call.args[0] for call in mock_sleep.call_args_list], [0.5, 1.0])

    @override_settings(
        WEATHER_MAX_RETRIES=2,
        WEATHER_MAX_RETRY_DELAY_SECONDS=10,
    )
    @patch("services.weather.weather_service.time.sleep")
    @patch("services.weather.weather_service.requests.get")
    def test_does_not_retry_before_an_excessive_retry_after_delay(self, mock_get, mock_sleep):
        throttled = Mock()
        throttled.status_code = 429
        throttled.headers = {"Retry-After": "30"}
        mock_get.return_value = throttled

        with self.assertRaises(WeatherProviderError):
            get_weather_for_points([
                {"lat": 19.0760, "lon": 72.8777, "when": "2026-11-27T12:00:00Z"}
            ])

        self.assertEqual(mock_get.call_count, 1)
        mock_sleep.assert_not_called()
