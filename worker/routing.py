from django.urls import path

from .consumers import TaskTransferConsumer, ObjectDetectionConsumer #VideoConsumer

ws_urlpatterns = [ 
  path('ws/video/', ObjectDetectionConsumer.as_asgi()), #${task_id}
  path('ws/task-transfer/<str:line_name>', TaskTransferConsumer.as_asgi()),
]
