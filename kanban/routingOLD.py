from django.urls import re_path, path

from . import consumers

websocket_urlpatterns = [
    re_path(r'^api/dash/project/(?P<pf>\w+)/(?P<prjct>\w+)/$', consumers.BoardConsumer.as_asgi()),
]