from django.urls import path

from .consumers import VideoConsumer, TaskTransferConsumer

ws_urlpatterns = [ 
  path('ws/video/<str:room_name>', VideoConsumer.as_asgi()),
  path('ws/task-transfer/<str:line_name>', TaskTransferConsumer.as_asgi()),
]
