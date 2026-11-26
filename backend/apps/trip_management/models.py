from django.db import models


class Trip(models.Model):
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    departure_time = models.DateTimeField()
    load_weight_lb = models.FloatField()
    sampling_interval_miles = models.IntegerField(default=25)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at"])]
