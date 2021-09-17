from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    name = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    phone_number = PhoneNumberField(blank=True)
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


# class UserNotification(models.Model):
#     pass # todo