import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tordi.settings')

# Must be created before importing anything that touches models/apps.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402
import chat.routing  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
