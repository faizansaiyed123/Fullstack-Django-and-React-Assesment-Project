from django.urls import path
from apps.routing.views import ForecastView, HealthView, PlanRouteView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("plan-route/", PlanRouteView.as_view(), name="plan-route"),
    path("forecast/", ForecastView.as_view(), name="forecast"),
]
