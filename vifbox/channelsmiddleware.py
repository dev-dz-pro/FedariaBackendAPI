from vifApp.models import User
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.db import close_old_connections
from urllib.parse import parse_qs
import jwt
from django.conf import settings


@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections() # Close old database connections to prevent usage of timed out connections
        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
        try:
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except (jwt.DecodeError, jwt.ExpiredSignatureError, KeyError):
            return None
        scope["user"] = await get_user(user_id=decoded_data["id"])
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))