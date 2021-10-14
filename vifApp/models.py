from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime


class User(AbstractUser):
    is_verified = models.BooleanField(default=False)
    email = models.CharField(max_length=255, blank=True, null=True)
    social_id = models.BigIntegerField(blank=True, null=True)
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    # profile_image = models.ImageField(default="default.jpg", upload_to="profile_pics")
    profile_image = models.URLField(max_length=600, default="https://vifbox.org/api/media/default.jpg")
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