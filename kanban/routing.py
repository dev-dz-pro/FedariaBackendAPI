from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'^api/dash/workspaces/(?P<workspace>[0-9a-f-]+)/portfolios/(?P<portfolio>[0-9a-f-]+)/projects/(?P<project>[0-9a-f-]+)/$', consumers.BoardConsumer.as_asgi()),
    re_path(r'^api/ws/dash/$', consumers.UserConsumer.as_asgi()),
]