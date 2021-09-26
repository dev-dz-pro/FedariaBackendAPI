from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
import datetime



class User(AbstractUser):
    is_verified = models.BooleanField(default=False)
    email = models.CharField(max_length=255, unique=True, blank=True, null=True)
    github_id = models.BigIntegerField(unique=True, blank=True, null=True)
    phone_number = PhoneNumberField(blank=True)
    # profile_image = models.CharField(max_length=255)
    # profile_image = models.ImageField(default="default.jpg", upload_to="profile_pics")
    profile_image = models.ImageField()
    profile_title = models.CharField(max_length=255)
    company_email = models.EmailField(blank=True)
    company_name = models.CharField(max_length=255, blank=True)


class UserNotification(models.Model):
    notification_user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_text = models.CharField(max_length=200)
    notification_from = models.CharField(max_length=200)
    notification_url = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    def was_published_today(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=1)
    def __str__(self):
        return self.notification_text
