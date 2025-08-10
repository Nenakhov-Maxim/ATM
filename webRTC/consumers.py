import json
import asyncio
import cv2
import numpy as np
import logging
import warnings
from fractions import Fraction

from channels.generic.websocket import AsyncWebsocketConsumer
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, MediaStreamTrack, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
from av import VideoFrame

# Suppress specific aiortc/asyncio warnings and errors
# warnings.filterwarnings("ignore", category=DeprecationWarning)
# logging.getLogger('aiortc').setLevel(logging.ERROR)
# logging.getLogger('aioice').setLevel(logging.ERROR)

# # Monkey patch to suppress the specific transport error
# import sys
# def custom_excepthook(exc_type, exc_value, exc_traceback):
#     if "SelectorDatagramTransport" in str(exc_value) or "AssertionError" in str(exc_type.__name__):
#         # Suppress this specific error as it's a known aiortc issue
#         return
#     sys.__excepthook__(exc_type, exc_value, exc_traceback)

# sys.excepthook = custom_excepthook

# Загрузка модели YOLO (или другой модели обнаружения объектов)
# TODO: Замените пути на ваши фактические пути к файлам модели
# net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
# classes = []
# with open("coco.names", "r") as f:
#     classes = [line.strip() for line in f.readlines()]
# layer_names = net.getLayerNames()
# output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

class ServerVideoTrack(VideoStreamTrack):
    """
    A video track that generates frames from server-side processing
    """
    def __init__(self, source_track=None):
        super().__init__()
        self.source_track = source_track
        self.frame_count = 0
        
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
        # Example: Add a simple overlay
        height, width = img.shape[:2]
        
        # Add timestamp
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(img, f"Server Processing: {timestamp}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add frame counter
        cv2.putText(img, f"Frame: {self.frame_count}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        # Example: Add a rectangle (simulating object detection)
        cv2.rectangle(img, (100, 100), (300, 200), (0, 0, 255), 2)
        cv2.putText(img, "Detected Object", (105, 95), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        self.frame_count += 1
        return img
    
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
                asyncio.ensure_future(self.test_video_reception(relayed_track))
        
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
                objects = self.detect_objects(img)

                # Отправка результатов обнаружения объектов клиенту
                await self.send(text_data=json.dumps({
                    "type": "detection_result",
                    "objects": objects
                }))

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
