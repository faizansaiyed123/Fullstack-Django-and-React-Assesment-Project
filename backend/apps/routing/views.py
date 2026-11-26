from __future__ import annotations

import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.routing.serializers import ForecastSerializer, PlanRouteSerializer
from apps.routing.services import forecast_corridor, plan_route
from services.geocoding.geocoding_service import GeocodingError
from services.routing.routing_service import RoutingProviderError
from services.weather.weather_service import WeatherProviderError

logger = logging.getLogger(__name__)

class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "timestamp": timezone.now().isoformat()})

class PlanRouteView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = PlanRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            result = plan_route(
                origin_query=data["origin"],
                destination_query=data["destination"],
                departure_time=data["departure_time"],
                load_weight_lb=data["load_weight_lb"],
                sampling_interval_miles=int(data["sampling_interval_miles"]),
            )
        except GeocodingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except WeatherProviderError:
            logger.exception("Weather provider failed during route planning")
            return Response({"error": "Unable to verify weather for this trip. Please try again."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except RoutingProviderError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception:
            logger.exception("Unexpected route planning failure")
            return Response({"error": "Unable to plan this trip right now."}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(result)

class ForecastView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ForecastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            return Response({
                "forecast_offset_hours": data["forecast_offset_hours"],
                "points": forecast_corridor(
                    departure_time=data["departure_time"],
                    forecast_offset_hours=data["forecast_offset_hours"],
                    points=data["points"],
                    load_weight_lb=data["load_weight_lb"],
                ),
            })
        except WeatherProviderError:
            logger.exception("Weather provider failed during corridor forecast")
            return Response({"error": "Unable to verify forecast for this hour. Please try again."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception("Unexpected corridor forecast failure")
            return Response({"error": "Unable to load corridor weather right now."}, status=status.HTTP_502_BAD_GATEWAY)
