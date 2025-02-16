"""
ASGI config for app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django_asgi_app = get_asgi_application()

from worker.routing import ws_urlpatterns

application = ProtocolTypeRouter({
  'http': get_asgi_application(),
  'websocket': AuthMiddlewareStack(
    URLRouter(ws_urlpatterns)
  )
})
