from django.urls import path

from .consumers import TaskTransferConsumer, ObjectDetectionConsumer

# WebSocket маршруты для приложения worker
ws_urlpatterns = [ 
    # Маршрут для обнаружения объектов через WebRTC
    path('ws/video/', ObjectDetectionConsumer.as_asgi()),
    # Маршрут для передачи информации о задачах в реальном времени
    path('ws/task-transfer/<str:line_name>', TaskTransferConsumer.as_asgi()),
]
