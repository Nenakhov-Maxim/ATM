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



class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.model = YOLO("AiVision/yolo_weights/t-profile_320_16.pt")
        self.task_id = -1
        self.max_id_profile = 0
        self.amount_profile = 0
        self.as_profile_yolo = {'Т-профиль':'t-profile__v11.pt'}
        
        

    async def disconnect(self, close_code=None):  #close_code
        pass       

    async def receive(self, text_data):        
        data = json.loads(text_data)                
        if data['isFs'] ==  1:  
            #print('Первая отправка сообщения')          
            self.task_id = data['task_id']
            self.amount_profile = await self.get_start_profile_amount()
            self.is_acc_pr = await self.is_accept_profile()
            
            if self.is_acc_pr == False:
                await self.send(text_data=json.dumps({
                    'error': 'Для данного профиля не поддерживается автоматическое распознование'
                }))
                await self.close(code=4123)
                
        elif data['chgVal'] ==  1:
            #print('Изменение количества профиля')
            self.amount_profile = data['value']
            await self.change_profile_amount_in_db()            
        else:                 
            image_data = data['image']

        # Декодирование изображения
            image_data = base64.b64decode(image_data)
            np_image = np.frombuffer(image_data, np.uint8)

        # Преобразование в изображение OpenCV
            frame = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

        # Обработка изображения с помощью YOLO
            processed_frame = self.process_frame(frame)

        # Дополнительная обработка или отправка результата обратно клиенту
        # закодировать обратно в base64 и отправить клиенту
        
            _, buffer = cv2.imencode('.jpg', processed_frame)
            processed_image_data = base64.b64encode(buffer).decode('utf-8')

            await self.send(text_data=json.dumps({
                'processed_image': processed_image_data,
                'max_id_profile': self.amount_profile
            }))

    def process_frame(self, frame):
    # Логика обработки изображения
    # Предобученная модель Yolov8      
        results = self.model.track(frame, stream=True, persist=True, iou=0.50, conf=0.88,
                                        tracker="botsort.yaml", imgsz=640, classes=0, verbose=False)
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
        return image
    
    @sync_to_async
    def get_start_profile_amount(self):
        return Tasks.objects.get(id=self.task_id).profile_amount_now
    
    @sync_to_async
    def is_accept_profile(self):
        profile = Tasks.objects.get(id=self.task_id).task_profile_type
        accepted_profile_list = AcceptedProfile.objects.get(type_profile=profile.association_name)
        if accepted_profile_list:
            print(accepted_profile_list.names_profile.split(','))
            print(profile.profile_name)
            print(profile.profile_name in accepted_profile_list.names_profile.split(','))
            if profile.profile_name in accepted_profile_list.names_profile.split(','):
                self.model = YOLO(f'AiVision/yolo_weights/{self.as_profile_yolo[profile.association_name]}')
                return True
            else:
                return False
        return False
    
    @sync_to_async
    def change_profile_amount_in_db(self):
        data_task = DatabaseWork({'id_task':self.task_id})    
        result = data_task.change_profile_amount(self.task_id, self.amount_profile)
        #print(result)

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