from typing import TYPE_CHECKING
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

# Create your models here.
class User(AbstractUser):
    pass