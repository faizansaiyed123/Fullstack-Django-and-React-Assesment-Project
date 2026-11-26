from rest_framework import serializers

class PlanRouteSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=255)
    destination = serializers.CharField(max_length=255)
    departure_time = serializers.DateTimeField()
    load_weight_lb = serializers.FloatField(min_value=1, max_value=200_000)
    sampling_interval_miles = serializers.ChoiceField(choices=(10, 25, 50), default=25)

class ForecastSerializer(serializers.Serializer):
    departure_time = serializers.DateTimeField()
    forecast_offset_hours = serializers.IntegerField(min_value=0, max_value=48)
    load_weight_lb = serializers.FloatField(min_value=1, max_value=200_000)
    points = serializers.ListField(child=serializers.DictField(), allow_empty=False, max_length=300)

    def validate_points(self, points):
        for point in points:
            if not {"lat", "lon", "route_id"} <= point.keys():
                raise serializers.ValidationError("Each point requires route_id, lat, and lon")
            try:
                lat = float(point["lat"]); lon = float(point["lon"])
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError("Coordinates must be numeric") from exc
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise serializers.ValidationError("Coordinate out of range")
        return points
