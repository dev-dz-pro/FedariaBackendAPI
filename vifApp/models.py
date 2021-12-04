from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime
from .utils import VifUtils 
from vifbox import settings
import requests
from urllib.parse import urlparse


class User(AbstractUser):
    is_verified = models.BooleanField(default=False)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=255, unique=True) # , blank=True, null=True
    social_id = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    profile_image = models.URLField(max_length=600, default="https://vifbox.org/api/media/default.jpg") # profile_image = models.ImageField(default="default.jpg", upload_to="profile_pics")
    profile_title = models.CharField(max_length=255)
    company_email = models.EmailField(blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    STATUS_CHOICES = [('Available', 'Available'), ('Busy', 'Busy'), ('Do not disturb', 'Do not disturb'), ('Away', 'Away')]
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='Available') 

    def get_presigned_url_img(self):
        if not self.profile_image.startswith("https://vifbox-backend.s3.amazonaws.com"):
            return self.profile_image
        res = requests.get(self.profile_image)
        if res.status_code <= 200:
            return self.profile_image
        else:
            file_aws_name = urlparse(self.profile_image).path[1:]
            utls_cls = VifUtils()
            return utls_cls.create_presigned_url(bucket_name=settings.BUCKET_NAME, region_name=settings.REGION_NAME, object_name=file_aws_name, expiration=600000)



class UserNotification(models.Model):
    notification_user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    notification_text = models.CharField(max_length=500)
    notification_url = models.CharField(max_length=350)
    notification_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def was_published_today(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=1)
    def __str__(self):
        return self.notification_text