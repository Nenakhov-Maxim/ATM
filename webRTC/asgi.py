import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import webRTC.routing as wrt

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_vision_RTC.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        wrt.websocket_urlpatterns
    ),
})