import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from . import urls

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            urls.websocket_urlpatterns
        )
    )
})