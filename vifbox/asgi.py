from django.urls import re_path, path
from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from .channelsmiddleware import JwtAuthMiddlewareStack
from kanban import routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JwtAuthMiddlewareStack(
        URLRouter(routing.websocket_urlpatterns)
    ),
})