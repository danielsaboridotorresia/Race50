from typing import TYPE_CHECKING
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

# Create your models here.
class User(AbstractUser):
    pass

class Session(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    external_id = models.CharField(max_length=128, null=True, blank=True)
    track_name = models.CharField(max_length=100)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Lap(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="laps")
    lap_no = models.PositiveIntegerField()
    lap_time_ms = models.PositiveIntegerField()
    s1_ms = models.PositiveIntegerField()
    s2_ms = models.PositiveIntegerField()
    s3_ms = models.PositiveIntegerField()
    valid = models.BooleanField(default=True)