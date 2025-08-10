from django.urls import re_path, path
from . import consumers

print('routing')

websocket_urlpatterns = [
    path('ws/object_detection/', consumers.ObjectDetectionConsumer.as_asgi()),
    # re_path(r'ws/object_detection/$', consumers.ObjectDetectionConsumer.as_asgi()),
]