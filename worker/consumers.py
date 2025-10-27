import json
import base64
import numpy as np
import cv2
import torch
from asgiref.sync import sync_to_async
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from ultralytics import YOLO
from master.databaseWork import DatabaseWork
from master.models import Tasks, AcceptedProfile

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay
from av import VideoFrame
from fractions import Fraction


class ServerVideoTrack(VideoStreamTrack):
    """
    Видеодорожка, которая генерирует кадры с серверной обработкой
    """
    def __init__(self, source_track=None, model_name=None, type_profile=None):
        super().__init__()
        self.source_track = source_track
        self.frame_count = 0
        self.max_id_profile = 0
        self.amount_profile = 0
        self.counter_cuda = 0
        self.type_profile = type_profile
        print(model_name)
        print(type_profile)
        if model_name == '' or model_name == None:
            self.model_name = 't-profile_240_nano_b=32.pt'
        else:
            self.model_name = model_name   
        self.model = YOLO(f"AiVision/yolo_weights/{self.model_name}")
        
    async def recv(self):
        """
        Генерирует и возвращает видеокадры для отправки клиенту
        """
        if self.source_track:
            # Получаем кадр из исходной дорожки (видео клиента)
            frame = await self.source_track.recv()
            
            # Конвертируем в numpy массив для обработки
            img = frame.to_ndarray(format="bgr24")
            
            # Обрабатываем кадр с помощью ИИ/компьютерного зрения
            processed_img = self.process_frame(img)
            
            # Конвертируем обратно в VideoFrame
            new_frame = VideoFrame.from_ndarray(processed_img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            
            return new_frame
        else:
            # Генерируем синтетические видеокадры (для тестирования)
            return await self.generate_synthetic_frame()
    
    def process_frame(self, img):
        """
        Обрабатывает кадр с помощью алгоритмов ИИ/компьютерного зрения
        """
        # Балансировка нагрузки между GPU
        if torch.cuda.is_available():
            print(f'Всего устройств для обработки: {torch.cuda.device_count()}')
            if self.counter_cuda == 0:
                torch.cuda.device(0)
                self.counter_cuda = 1
                print(f'Обработка на видеокарте № 1: {torch.cuda.get_device_name(0)}')
            else:
                torch.cuda.device(1)
                self.counter_cuda = 0
                print(f'Обработка на видеокарте № 2: {torch.cuda.get_device_name(1)}')
        
        # Логика обработки изображения с помощью предобученной модели YOLOv8      
        results = self.model.track(img, stream=True, persist=True, iou=0.60, conf=0.83,
                                  tracker="botsort.yaml", imgsz=256, classes=0, verbose=False)
        
        for result in results:
            res_plotted = result.plot()
            if result.boxes.id is not None:
                for id_item in result.boxes.id:
                    id_item = int(id_item.item())                    
                    if id_item > self.max_id_profile:
                        self.amount_profile += (id_item - self.max_id_profile)
                        self.max_id_profile = id_item
                        
        # Изменяем размер изображения для оптимизации
        res_plotted = cv2.resize(res_plotted, (res_plotted.shape[1]//2, res_plotted.shape[0]//2))
        
        # Добавляем временную метку
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(res_plotted, f"Server timedate: {timestamp}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)       
        
        # Добавляем счетчик профилей
        cv2.putText(res_plotted, f"Number profile visible: {self.max_id_profile}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        
        # Добавляем тип профиля
        cv2.putText(res_plotted, f"Type profile: {self.type_profile}", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        
        # Добавляем тип профиля
        cv2.putText(res_plotted, f"Model type: {self.model_name}", 
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        
        return res_plotted
    
    async def generate_synthetic_frame(self):
        """
        Генерирует синтетические кадры когда исходная дорожка недоступна
        """
        width, height = 640, 480
        
        # Создаем градиентный фон
        img = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(height):
            img[i, :] = [i * 255 // height, 100, 255 - (i * 255 // height)]
        
        # Добавляем текст
        cv2.putText(img, f"Сгенерированный кадр сервера: {self.frame_count}", 
                   (50, height//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Конвертируем в VideoFrame
        frame = VideoFrame.from_ndarray(img, format="bgr24")
        frame.pts = self.frame_count
        frame.time_base = Fraction(1, 30)  # 30 FPS
        
        self.frame_count += 1
        
        # Добавляем задержку для контроля частоты кадров
        await asyncio.sleep(1/30)  # 30 FPS
        
        return frame

class ObjectDetectionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket потребитель для обнаружения объектов с использованием WebRTC
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pc = None
        self.relay = MediaRelay()
        self.server_video_track = None
        
        # Настройка asyncio для корректной обработки ошибок транспорта
        try:
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(self._handle_exception)
        except RuntimeError:
            # Если цикл событий не запущен, это будет установлено при запуске цикла
            pass
    
    def _handle_exception(self, loop, context):
        """Пользовательский обработчик исключений для подавления ошибок транспорта"""
        exception = context.get('exception')
        if exception:
            if 'SelectorDatagramTransport' in str(exception) or 'AssertionError' in str(type(exception).__name__):
                # Подавляем эту конкретную ошибку
                return
        # Для других исключений используем обработку по умолчанию
        loop.default_exception_handler(context)

    async def connect(self):
        await self.accept()
        print("WebSocket подключен")

    async def disconnect(self, close_code):
        print("WebSocket отключен")
        if self.pc:
            await self.pc.close()

    async def receive(self, text_data):
        message = json.loads(text_data)
        print(f"Получено сообщение: {message}")

        if message["type"] == "offer":
            self.task_id = message["task_id"]
            self.profile_type = await sync_to_async(lambda: Tasks.objects.get(id=self.task_id).task_profile_type.profile_name)()
            self.model_name = await sync_to_async(lambda: Tasks.objects.get(id=self.task_id).task_profile_type.yolo_model_name)()
            await self.create_peer_connection(message["sdp"])
        elif message["type"] == "answer":
            print('Получен ответ SDP')
            await self.set_remote_description(message["sdp"])
        elif message["type"] == "candidate":
            await self.add_ice_candidate(message["candidate"])

    async def create_peer_connection(self, offer_sdp):
        """Создает WebRTC соединение с настройкой ICE серверов"""
        try:
            # Настройка ICE серверов для максимальной совместимости
            ice_servers = [
                # Google STUN серверы
                RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
                
                RTCIceServer(
                    urls=['turn:192.168.0.9:3478?transport=udp', 'turn:192.168.0.9:3478?transport=tcp', 'turn:192.168.0.9:5349?transport=tcp'],
                    username="maxim", 
                    credential="7510897575Max"
                ),
            ]
            
            configuration = RTCConfiguration(iceServers=ice_servers)
            self.pc = RTCPeerConnection(configuration=configuration)
            print("RTCPeerConnection создан с STUN/TURN серверами")
        except Exception as e:
            print(f"Ошибка создания RTCPeerConnection с STUN/TURN: {e}")
            # Резервная конфигурация для локальной разработки
            try:
                configuration = RTCConfiguration(iceServers=[])
                self.pc = RTCPeerConnection(configuration=configuration)
                print("RTCPeerConnection создан с локальной конфигурацией")
            except Exception as e2:
                print(f"Ошибка создания локального RTCPeerConnection: {e2}")
                raise e2
        
        # Добавляем серверную видеодорожку
        self.server_video_track = ServerVideoTrack(model_name=self.model_name, type_profile=self.profile_type)
        self.pc.addTrack(self.server_video_track)
        print("Серверная видеодорожка добавлена в peer connection")
    
        @self.pc.on("track")
        async def on_track(track):
            print(f"Получена дорожка {track.kind} - ID: {track.id}")
            
            if track.kind == "video":
                print("Обработка видеодорожки...")
                # Обновляем серверную видеодорожку с полученным видеоисточником
                relayed_track = self.relay.subscribe(track)
                
                # Важно: обновляем источник существующей серверной видеодорожки
                if self.server_video_track:
                    self.server_video_track.source_track = relayed_track
                    print("Серверная видеодорожка обновлена с видеоисточником клиента")
                else:
                    print("Предупреждение: server_video_track равен None")
                
                # Запускаем обработку кадров для результатов обнаружения
                asyncio.ensure_future(self.frame_worker(relayed_track))
        
        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            print(f"Состояние ICE соединения: {self.pc.iceConnectionState}")
            if self.pc.iceConnectionState == "failed":
                print("ICE соединение не удалось - возможны проблемы с NAT/firewall")
                await self.pc.close()
            elif self.pc.iceConnectionState == "connected":
                print("ICE соединение успешно установлено")
            elif self.pc.iceConnectionState == "disconnected":
                print("ICE соединение отключено")

        @self.pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange():
            print(f"Состояние сбора ICE: {self.pc.iceGatheringState}")
            if self.pc.iceGatheringState == "complete":
                print("Сервер: Все ICE кандидаты собраны")

        @self.pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                print(f"Сервер сгенерировал ICE кандидата: {candidate.type} - {candidate.ip}:{candidate.port}")
                # Отправляем ICE кандидата сервера клиенту
                candidate_dict = {
                    'candidate': candidate.candidate,
                    'foundation': candidate.foundation,
                    'ip': candidate.ip,
                    'port': candidate.port,
                    'protocol': candidate.protocol,
                    'type': candidate.type,
                    'priority': candidate.priority,
                    'component': candidate.component,
                    'sdpMid': candidate.sdpMid,
                    'sdpMLineIndex': candidate.sdpMLineIndex,
                    'tcpType': candidate.tcpType
                }
                await self.send(text_data=json.dumps({
                    "type": "candidate",
                    "candidate": candidate_dict
                }))
            else:
                print("Сервер: Сбор ICE кандидатов завершен")

        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
        await self.pc.setRemoteDescription(offer)
        
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        
        ld_sdp = self.pc.localDescription.sdp
        js_answer = {
            "type": "answer",
            "sdp": ld_sdp
        }
        await self.send(text_data=json.dumps(js_answer))
    
    async def set_remote_description(self, answer_sdp):
        """Устанавливает удаленное описание SDP"""
        print('Установка удаленного описания SDP')
        answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
        await self.pc.setRemoteDescription(answer)

    async def add_ice_candidate(self, candidate):
        """Добавляет ICE кандидата для установления соединения"""
        try:
            if isinstance(candidate, str):
                candidate = {'candidate': candidate}
            print(f"Сервер: добавление ICE кандидата: {candidate}")
            await self.pc.addIceCandidate(candidate)
            print(f"ICE кандидат успешно добавлен: {candidate.get('type', '<нет-типа>')}")
        except Exception as e:
            print(f"Ошибка добавления ICE кандидата: {e}")
            # Продолжаем без этого кандидата - WebRTC может работать с частичными кандидатами
    
    async def frame_worker(self, track):
        """Обрабатывает видеокадры для обнаружения объектов"""
        while True:
            try:
                frame = await track.recv()
                # Преобразование кадра aiortc.mediastreams.VideoFrame в изображение OpenCV
                img = frame.to_ndarray(format="bgr24")

                # Здесь можно добавить вызов функции обнаружения объектов
                # objects = self.detect_objects(img)

                # Отправка результатов обнаружения объектов клиенту
                # await self.send(text_data=json.dumps({
                #     "type": "detection_result",
                #     "objects": objects
                # }))

            except Exception as e:
                print(f"Ошибка обработки кадра: {e}")
                break
            
    async def test_video_reception(self, track):
        """Тестовый метод для проверки получения видеокадров"""
        frame_count = 0
        try:
            while frame_count < 10:  # Тестируем первые 10 кадров
                frame = await track.recv()
                frame_count += 1
                print(f"Тест: Получен кадр {frame_count} - Размер: {frame.width}x{frame.height}")
                await asyncio.sleep(0.1)  # Небольшая задержка
        except Exception as e:
            print(f"Ошибка тестового получения видео: {e}")
    
    def detect_objects(self, img):
        """Заглушка для функции обнаружения объектов"""
        objects = []
        return objects


# Глобальный список задач для отслеживания изменений
task_list = []

class TaskTransferConsumer(AsyncWebsocketConsumer):
    """
    WebSocket потребитель для передачи информации о задачах в реальном времени
    """
    async def connect(self):
        """Подключение клиента к WebSocket"""
        await self.accept()  
        await self.send(text_data=json.dumps({
            'type': 'Welcome',            
        }))      
        self.client = self.scope['client']
        self.area_id = self.scope['url_route']['kwargs']
        self.task_list = []
        self.profile_quantity_old = 0

    async def disconnect(self, close_code):
        """Отключение клиента от WebSocket"""
        pass    
    
    async def receive(self, text_data):
        """Получение сообщения от клиента"""        
        data = json.loads(text_data)
        if data['message'] == "start":         
            self.task_list = data['task_list']            
            await self.check_new_task()
            
    
    async def check_new_task(self):
        """Проверяет новые задачи и изменения в существующих задачах каждые 10 секунд"""        
        global task_list                     
        while True:
            await self.check_profile_amount()
            await asyncio.sleep(1)
            
            # Проверяем новые задачи
            db_task = await self.get_all_task()                        
            if len(db_task) > 0:
                for task in db_task:                                                
                    task_list[str(task['id'])] = str(task['task_status_id'])                    
                    await self.send(text_data=json.dumps({
                        'type': 'new_task',
                        'content': task            
                    }, default=str))
                      
            # Проверяем изменения в существующих задачах
            db_task_ch = await self.get_task_with_id()
            if len(db_task_ch) > 0:
                for task in db_task_ch:                     
                    task_list[str(task['id'])] = str(task['task_status_id'])                    
                    await self.send(text_data=json.dumps({
                        'type': 'change_task',
                        'content': task            
                    }, default=str))
   
    async def check_profile_amount(self):
        profile_amount = await self.get_only_working_task()
        if not self.profile_quantity_old == int(profile_amount):
            self.profile_quantity_old = int(profile_amount)
            await self.send(text_data=json.dumps({
                        'type': 'change_profile_amount',
                        'content': profile_amount            
                    }, default=str))
                         
    # Смотрим сколько профиля в данный момент в выполняемой задаче
    @sync_to_async
    def get_only_working_task(self):
        profile_amount = 0
        tasks = Tasks.objects.filter(
                task_workplace=self.area_id['line_name'], 
                task_status_id__in=[3],
            )
        for task in tasks:
            profile_amount = task.profile_amount_now
        return profile_amount
        
    
    @sync_to_async
    def get_all_task(self):
        """Получает все новые задачи для данной производственной линии"""
        global task_list
        task_list = self.task_list        
        query_task = []
        tasks = Tasks.objects.filter(
            task_workplace=self.area_id['line_name'], 
            task_status_id__in=[3, 4, 7]
        )
        
        for task in tasks:
            if str(task.id) not in task_list.keys():
                content = {
                    'id': task.id, 
                    'name': task.task_name, 
                    'task_status': task.task_status.status_name, 
                    'task_status_id': task.task_status_id, 
                    'task_name': task.task_name,
                    'task_profile_type': task.task_profile_type.profile_name, 
                    'task_timedate_start': task.task_timedate_start,
                    'task_timedate_end': task.task_timedate_end, 
                    'task_profile_amount': task.task_profile_amount,
                    'task_timedate_end_fact': task.task_timedate_end_fact, 
                    'task_time_settingUp': task.task_time_settingUp,
                    'task_timedate_start_fact': task.task_timedate_start_fact, 
                    'profile_amount_now': task.profile_amount_now,
                    'task_workplace_id': task.task_workplace_id
                }
                query_task.append(content)
                     
        return query_task
    
    @sync_to_async
    def get_task_with_id(self):
        """Получает задачи с изменившимся статусом"""        
        global task_list
        task_list = self.task_list        
        query_task = []
        
        for task_id in task_list.keys():
            if task_list[task_id] in ['3', '7']:                               
                task = Tasks.objects.get(id=task_id)                   
                if str(task.task_status_id) != task_list[task_id]:                    
                    content = {
                        'id': task.id, 
                        'name': task.task_name, 
                        'task_status': task.task_status.status_name, 
                        'task_status_id': task.task_status_id, 
                        'task_name': task.task_name,
                        'task_profile_type': task.task_profile_type.profile_name, 
                        'task_timedate_start': task.task_timedate_start,
                        'task_timedate_end': task.task_timedate_end, 
                        'task_profile_amount': task.task_profile_amount,
                        'task_timedate_end_fact': task.task_timedate_end_fact, 
                        'task_time_settingUp': task.task_time_settingUp,
                        'task_timedate_start_fact': task.task_timedate_start_fact, 
                        'profile_amount_now': task.profile_amount_now,
                        'task_workplace_id': task.task_workplace_id
                    }
                    query_task.append(content)
                     
        return query_task
