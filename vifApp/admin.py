from django.contrib import admin
from .models import UserNotification, User

admin.site.register(User)
admin.site.register(UserNotification)
