from typing import TYPE_CHECKING
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

# Create your models here.
class User(AbstractUser):
    pass


class Session(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    external_id = models.CharField(max_length=200, null=True, blank=True)
    track = models.CharField(max_length=100)
    date = models.DateField()

    laps_count = models.PositiveIntegerField()
    best_lap_ms = models.PositiveIntegerField()
    best_lap_number = models.PositiveIntegerField()
    worst_lap_ms = models.PositiveIntegerField()
    avg_lap_ms = models.PositiveIntegerField()
    tbl_ms = models.PositiveIntegerField()
    consistency_percent = models.FloatField()

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "date"])]

    def __str__(self):
        return f"{self.track} @ {self.date} ({self.user})"


class Lap(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="laps")
    lap = models.PositiveIntegerField()
    s1_ms = models.PositiveIntegerField()
    s2_ms = models.PositiveIntegerField()
    s3_ms = models.PositiveIntegerField()
    total_ms = models.PositiveIntegerField()
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [("session", "lap")]
        indexes = [models.Index(fields=["session", "lap"])]

    def __str__(self):
        return f"Lap {self.lap} — {self.total_ms} ms"