from django.urls import re_path, path
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from .channelsmiddleware import JwtAuthMiddlewareStack
from kanban import routing


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JwtAuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)
        ),
    ),
})