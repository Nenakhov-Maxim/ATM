import json
from random import randint
from time import sleep
import base64
import numpy as np
import cv2
import torch
from asgiref.sync import sync_to_async
import asyncio

from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from ultralytics import YOLO
from master.databaseWork import DatabaseWork
from master.models import *
from master.models import Tasks, AcceptedProfile

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, MediaStreamTrack, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
from av import VideoFrame
from fractions import Fraction


class ServerVideoTrack(VideoStreamTrack):
    """
    A video track that generates frames from server-side processing
    """
    def __init__(self, source_track=None):
        super().__init__()
        self.source_track = source_track
        self.frame_count = 0
        self.model = YOLO("AiVision/yolo_weights/t-profile_240_nano_b=32.pt")
        self.task_id = -1
        self.max_id_profile = 0
        self.amount_profile = 0
        self.as_profile_yolo = {'Т-профиль':'t-profile_240_nano_b=32.pt'}
        self.counter_cuda = 0
        self.type_profile = 'T-profile'
        
    async def recv(self):
        """
        Generate and return video frames to send to client
        """
        
        if self.source_track:
            # Get frame from source track (client's video)
            frame = await self.source_track.recv()
            
            # Convert to numpy array for processing
            img = frame.to_ndarray(format="bgr24")
            
            # Process the frame (add your AI/computer vision processing here)
            processed_img = self.process_frame(img)
            
            # Convert back to VideoFrame
            new_frame = VideoFrame.from_ndarray(processed_img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            
            return new_frame
        else:
            # Generate synthetic video frames (for testing)
            return await self.generate_synthetic_frame()
    
    def process_frame(self, img):
        """
        Process the frame with AI/computer vision algorithms
        Add your object detection, image processing, etc. here
        """
        
        if torch.cuda.is_available():
            print(f'Всего устройст для обработки: {torch.cuda.device_count()}')
            if self.counter_cuda == 0:
                torch.cuda.device(0)
                self.counter_cuda = 1
                print(f'эта обработка на видеокарте № 1: {torch.cuda.get_device_name(0)}')
            else:
                torch.cuda.device(1)
                self.counter_cuda = 0
                print(f'эта обработка на видеокарте № 2: {torch.cuda.get_device_name(1)}')
        # else:
        #     print(f'Устройства CUDA не найдены')
        
        # Example: Add a simple overlay
        height, width = img.shape[:2]
        
        
    # Логика обработки изображения
    # Предобученная модель Yolov8      
        results = self.model.track(img, stream=True, persist=True, iou=0.50, conf=0.65,
                                        tracker="botsort.yaml", imgsz=240, classes=0, verbose=False)
        for result in results:
            res_plotted = result.plot()
            if result.boxes.id != None:
                for id_item in result.boxes.id:
                    id_item = int(id_item.item())                    
                    if id_item > self.max_id_profile:
                        self.amount_profile = self.amount_profile + (id_item - self.max_id_profile)
                        self.max_id_profile = id_item
                        
                        
        res_plotted = cv2.resize(res_plotted, (res_plotted.shape[1]//2, res_plotted.shape[0]//2))
        image = res_plotted 
        
        # Add timestamp
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(image, f"Server date: {timestamp}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)       
        
        
        # Add profile counter
        cv2.putText(image, f"Vision Profile: {self.max_id_profile}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        # Add type profile counter
        cv2.putText(image, f"Type Profile: {self.type_profile}", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        
        return image
        
        # # Example: Add a rectangle (simulating object detection)
        # cv2.rectangle(img, (100, 100), (300, 200), (0, 0, 255), 2)
        # cv2.putText(img, "Detected Object", (105, 95), 
        #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        
        
        # self.frame_count += 1
        # return img
    
    async def generate_synthetic_frame(self):
        """
        Generate synthetic frames when no source track is available
        """
        # Create a simple colored frame
        width, height = 640, 480
        
        # Create a gradient background
        img = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(height):
            img[i, :] = [i * 255 // height, 100, 255 - (i * 255 // height)]
        
        # Add some text
        cv2.putText(img, f"Server Generated Frame: {self.frame_count}", 
                   (50, height//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Convert to VideoFrame
        frame = VideoFrame.from_ndarray(img, format="bgr24")
        frame.pts = self.frame_count
        frame.time_base = Fraction(1, 30)  # 30 FPS
        
        self.frame_count += 1
        
        # Add delay to control frame rate
        await asyncio.sleep(1/30)  # 30 FPS
        
        return frame

class ObjectDetectionConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pc = None
        self.relay = MediaRelay()
        self.server_video_track = None
        # self.frame_queue = asyncio.Queue()
        
        # Configure asyncio to handle transport errors gracefully
        try:
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(self._handle_exception)
        except RuntimeError:
            # If no event loop is running, this will be set when the loop starts
            pass
    
    def _handle_exception(self, loop, context):
        """Custom exception handler to suppress transport errors"""
        exception = context.get('exception')
        if exception:
            if 'SelectorDatagramTransport' in str(exception) or 'AssertionError' in str(type(exception).__name__):
                # Suppress this specific error
                return
        # For other exceptions, use default handling
        loop.default_exception_handler(context)

    async def connect(self):
        await self.accept()
        print("WebSocket connected")

    async def disconnect(self, close_code):
        print("WebSocket disconnected")
        if self.pc:
            await self.pc.close()

    async def receive(self, text_data):
        message = json.loads(text_data)
        print(f"Received message: {message}")

        if message["type"] == "offer":
            await self.create_peer_connection(message["sdp"])
        elif message["type"] == "answer":
            print('message-sdp')
            await self.set_remote_description(message["sdp"])
        elif message["type"] == "candidate":
            await self.add_ice_candidate(message["candidate"])

    async def create_peer_connection(self, offer_sdp):
        
        # Configure ICE servers for maximum compatibility
        try:
            # Use comprehensive ICE server configuration
            ice_servers = [
                # Google STUN servers
                RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
                
                RTCIceServer(
                    urls=['turn:192.168.0.9:3478?transport=udp', 'turn:192.168.0.9:3478?transport=tcp', 'turn:192.168.0.9:5349?transport=tcp'],
                    username="maxim", 
                    credential="7510897575Max"
                ),
            ]
            
            configuration = RTCConfiguration(
                iceServers=ice_servers
            )
            
            self.pc = RTCPeerConnection(configuration=configuration)
            print("RTCPeerConnection created with STUN/TURN servers")
        except Exception as e:
            print(f"Error creating RTCPeerConnection with STUN/TURN: {e}")
            # Fallback to local-only configuration for development
            try:
                # For local development, try without ICE servers
                configuration = RTCConfiguration(
                    iceServers=[]
                )
                self.pc = RTCPeerConnection(configuration=configuration)
                print("RTCPeerConnection created with local configuration")
            except Exception as e2:
                print(f"Error creating local RTCPeerConnection: {e2}")
                raise e2
        
        # Add a placeholder server video track that will be updated when client track is received
        self.server_video_track = ServerVideoTrack()
        self.pc.addTrack(self.server_video_track)
        print("Added server video track to peer connection")
    
        @self.pc.on("track")
        async def on_track(track):
            print(f"Track {track.kind} received - ID: {track.id}")
            
            if track.kind == "video":
                print("Processing video track...")
                # Update the server video track with the received video source
                relayed_track = self.relay.subscribe(track)
                
                # Important: Update the existing server video track's source
                if self.server_video_track:
                    self.server_video_track.source_track = relayed_track
                    print("Server video track updated with client video source")
                else:
                    print("Warning: server_video_track is None")
                
                # Start frame processing for detection results
                asyncio.ensure_future(self.frame_worker(relayed_track))
                
                # Test if we can receive frames
                # asyncio.ensure_future(self.test_video_reception(relayed_track))
        
        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            print("ICE connection state is %s" % self.pc.iceConnectionState)
            if self.pc.iceConnectionState == "failed":
                print("ICE connection failed - this may be due to NAT/firewall issues")
                await self.pc.close()
            elif self.pc.iceConnectionState == "connected":
                print("ICE connection established successfully")
            elif self.pc.iceConnectionState == "disconnected":
                print("ICE connection disconnected")

        @self.pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange():
            print("ICE gathering state is %s" % self.pc.iceGatheringState)
            if self.pc.iceGatheringState == "complete":
                print("Server: All ICE candidates have been gathered")

        @self.pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                print(f"Server generated ICE candidate: {candidate.type} - {candidate.ip}:{candidate.port}")
                # Send the server's ICE candidate to the client
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
                print("Server: ICE candidate gathering completed")

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
        print('SET REMOTE DESCRIPTION')
        answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
        await self.pc.setRemoteDescription(answer)

    async def add_ice_candidate(self, candidate):
        try:
            if isinstance(candidate, str):
                candidate = {'candidate': candidate}
            print("Server: add_ice_candidate() got():", candidate)
            await self.pc.addIceCandidate(candidate) #ice_candidate
            print(f"ICE candidate added successfully: {candidate.get('type', '<no-type>')}")
        except Exception as e:
            print(f"Error adding ICE candidate: {e}")
            # Continue without this candidate - WebRTC can work with partial candidates
    
    async def frame_worker(self, track):
        
        while True:
            try:
                
                frame = await track.recv()
                # Преобразование кадра aiortc.mediastreams.VideoFrame в изображение OpenCV
                img = frame.to_ndarray(format="bgr24")

                # Вызов функции обнаружения объектов
                # objects = self.detect_objects(img)

                # Отправка результатов обнаружения объектов клиенту
                # await self.send(text_data=json.dumps({
                #     "type": "detection_result",
                #     "objects": objects
                # }))

            except Exception as e:
                print(f"Error processing frame: {e}")
                break
            
    async def test_video_reception(self, track):
        """Test method to verify we're receiving video frames"""
        frame_count = 0
        try:
            while frame_count < 10:  # Test first 10 frames
                frame = await track.recv()
                frame_count += 1
                print(f"Test: Received frame {frame_count} - Size: {frame.width}x{frame.height}")
                await asyncio.sleep(0.1)  # Small delay
        except Exception as e:
            print(f"Test video reception error: {e}")
    
    def detect_objects(self, img):
        objects = []
        return objects

        # TODO: Реализуйте логику обнаружения объектов здесь
        # Используйте OpenCV, TensorFlow, PyTorch или любую другую библиотеку
        # для обнаружения объектов на изображении.


task_list = []

class TaskTransferConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()  
        await self.send(text_data=json.dumps({
            'type': 'Welcome',            
        }))      
        self.client = self.scope['client']
        self.area_id = self.scope['url_route']['kwargs']
        self.task_list = []

    async def disconnect(self, close_code):
        pass    
    
    async def receive(self, text_data):        
        data = json.loads(text_data)
        if data['message'] == "start":         
            self.task_list = data['task_list']            
            await self.check_new_task() 
    
    async def check_new_task(self):        
        global task_list                     
        while True:
            await asyncio.sleep(10)
            db_task = await self.get_all_task()                        
            if len(db_task) > 0:
                #print('Нашли задачи') 
                for task in db_task:                                                
                    task_list[str(task['id'])] = str(task['task_status_id'])                    
                    await self.send(text_data=json.dumps({
                    'type': 'new_task',
                    'content': task            
                    }, default=str))
                      
            db_task_ch = await self.get_task_with_id()
            if len(db_task_ch) > 0:
                for task in db_task_ch:                     
                    task_list[str(task['id'])] = str(task['task_status_id'])                    
                    await self.send(text_data=json.dumps({
                    'type': 'change_task',
                    'content': task            
                    }, default=str))               
            # print(task_list) 
                        
    @sync_to_async
    def get_all_task(self):
        global task_list
        task_list = self.task_list        
        query_task = []
        tasks = Tasks.objects.all().filter(task_workplace=self.area_id['line_name'], task_status_id__in=[3, 4, 7])         
        for task in tasks:
            if str(task.id) not in task_list.keys():
                content = {'id':task.id, 'name': task.task_name, 'task_status': task.task_status.status_name, 'task_status_id': task.task_status_id, 'task_name': task.task_name,
                                  'task_profile_type': task.task_profile_type.profile_name, 'task_timedate_start': task.task_timedate_start,
                                  'task_timedate_end': task.task_timedate_end, 'task_profile_amount': task.task_profile_amount,
                                  'task_timedate_end_fact': task.task_timedate_end_fact, 'task_time_settingUp': task.task_time_settingUp,
                                  'task_timedate_start_fact': task.task_timedate_start_fact, 'profile_amount_now': task.profile_amount_now,
                                  'task_workplace_id': task.task_workplace_id}
                query_task.append(content)
                     
        return query_task
    
    @sync_to_async
    def get_task_with_id(self):        
        global task_list
        task_list = self.task_list        
        query_task = []
        for task_id in task_list.keys():
            if task_list[task_id] == '3' or task_list[task_id] == '7':                               
                task = Tasks.objects.get(id=task_id)                   
                if str(task.task_status_id) != task_list[task_id]:                    
                    content = {'id':task.id, 'name': task.task_name, 'task_status': task.task_status.status_name, 'task_status_id': task.task_status_id, 'task_name': task.task_name,
                                        'task_profile_type': task.task_profile_type.profile_name, 'task_timedate_start': task.task_timedate_start,
                                        'task_timedate_end': task.task_timedate_end, 'task_profile_amount': task.task_profile_amount,
                                        'task_timedate_end_fact': task.task_timedate_end_fact, 'task_time_settingUp': task.task_time_settingUp,
                                        'task_timedate_start_fact': task.task_timedate_start_fact, 'profile_amount_now': task.profile_amount_now,
                                        'task_workplace_id': task.task_workplace_id}
                    query_task.append(content)
                     
        return query_task
    
# class VideoConsumer(AsyncWebsocketConsumer):
#     async def connect(self):''
#         await self.accept()
#         self.model = YOLO("AiVision/yolo_weights/t-profile__v11.pt")
#         self.task_id = -1
#         self.max_id_profile = 0
#         self.amount_profile = 0
#         self.as_profile_yolo = {'Т-профиль':'t-profile__v11.pt'}
#         self.counter_cuda = 0
        
        

#     async def disconnect(self, close_code=None):  #close_code
#         pass       

#     async def receive(self, text_data):   
#         data = json.loads(text_data)                
#         if data['isFs'] ==  1:  
#             #Первая отправка сообщения         
#             self.task_id = data['task_id']
#             self.amount_profile = await self.get_start_profile_amount()
#             self.is_acc_pr = await self.is_accept_profile()
            
#             if self.is_acc_pr == False:
#                 await self.send(text_data=json.dumps({
#                     'error': 'Для данного профиля не поддерживается автоматическое распознование'
#                 }))
#                 await self.close(code=4123)
                
#         elif data['chgVal'] ==  1:
#             #Изменение количества профиля
#             self.amount_profile = data['value']
#             await self.change_profile_amount_in_db()            
#         else:                 
#             image_data = data['image']
#             if torch.cuda.is_available():
#                 print(f'Всего устройст для обработки: {torch.cuda.device_count()}')
#                 if self.counter_cuda == 0:
#                     torch.cuda.device(0)
#                     self.counter_cuda = 1
#                     print(f'эта обработка на видеокарте № 1: {torch.cuda.get_device_name(0)}')
#                 else:
#                     torch.cuda.device(1)
#                     self.counter_cuda = 0
#                     print(f'эта обработка на видеокарте № 2: {torch.cuda.get_device_name(1)}')
                

#         # Декодирование изображения
#             image_data = base64.b64decode(image_data)
#             np_image = np.frombuffer(image_data, np.uint8)

#         # Преобразование в изображение OpenCV
#             frame = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

#         # Обработка изображения с помощью YOLO
#             processed_frame = self.process_frame(frame)

#         # Дополнительная обработка или отправка результата обратно клиенту
#         # закодировать обратно в base64 и отправить клиенту
        
#             _, buffer = cv2.imencode('.jpg', processed_frame)
#             processed_image_data = base64.b64encode(buffer).decode('utf-8')

#             await self.send(text_data=json.dumps({
#                 'processed_image': processed_image_data,
#                 'max_id_profile': self.amount_profile
#             }))

#     def process_frame(self, frame):
#     # Логика обработки изображения
#     # Предобученная модель Yolov8      
#         results = self.model.track(frame, stream=True, persist=True, iou=0.50, conf=0.65,
#                                         tracker="botsort.yaml", imgsz=480, classes=0, verbose=False)
#         for result in results:
#             res_plotted = result.plot()
#             if result.boxes.id != None:
#                 for id_item in result.boxes.id:
#                     id_item = int(id_item.item())                    
#                     if id_item > self.max_id_profile:
#                         self.amount_profile = self.amount_profile + (id_item - self.max_id_profile)
#                         self.max_id_profile = id_item
                        
                        
#         res_plotted = cv2.resize(res_plotted, (res_plotted.shape[1]//2, res_plotted.shape[0]//2))
#         image = res_plotted        
#         return image
    
#     @sync_to_async
#     def get_start_profile_amount(self):
#         return Tasks.objects.get(id=self.task_id).profile_amount_now
    
#     @sync_to_async
#     def is_accept_profile(self):
#         profile = Tasks.objects.get(id=self.task_id).task_profile_type
#         accepted_profile_list = AcceptedProfile.objects.get(type_profile=profile.association_name)
#         if accepted_profile_list:
#             print(accepted_profile_list.names_profile.split(','))
#             print(profile.profile_name)
#             print(profile.profile_name in accepted_profile_list.names_profile.split(','))
#             if profile.profile_name in accepted_profile_list.names_profile.split(','):
#                 self.model = YOLO(f'AiVision/yolo_weights/{self.as_profile_yolo[profile.association_name]}')
#                 self.model.to('cuda')
#                 return True
#             else:
#                 return False
#         return False
    
#     @sync_to_async
#     def change_profile_amount_in_db(self):
#         data_task = DatabaseWork({'id_task':self.task_id})    
#         result = data_task.change_profile_amount(self.task_id, self.amount_profile)
#         #print(result)