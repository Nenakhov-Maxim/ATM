//Взаимодействие клиента с сервером по вебсоккету

$(document).ready(function() {
  let task_id_list = {}
  let name_line = document.querySelectorAll(".person-info__department")[1].dataset.line
  let tasks_list = document.querySelectorAll(".task-card-item")
  const socket_task = new WebSocket(`ws://192.168.211.1/ws/task-transfer/${name_line}`); //На сервере
  // const socket_task = new WebSocket(`ws://127.0.0.1:8000/ws/task-transfer/${name_line}`); //На домашней машине

  for (const key in tasks_list) {
    if (Object.prototype.hasOwnProperty.call(tasks_list, key)) {
      const element = tasks_list[key];      
      task_id_list[element.dataset.itemid] = element.dataset.categoryId      
    }
  }

  socket_task.onopen = function() {

    socket_task.send(JSON.stringify({message:"start", task_list:task_id_list}))

  socket_task.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type == "Welcome"){
      // alert(`Успешно подключились к серверу AT-Manager. Производственная линия № ${name_line}`)
    } else if (data.type == "new_task") {
      ws_add_new_task(data['content'])
    } else if  (data.type == 'change_task') {
      alert(`Статус задачи "${data['content']['task_name']}" № ${data['content']['id']} от ${data['content']['task_timedate_start']} изменен на "${data['content']['task_status']}"`)
      if (data['content']['task_status_id']==5 || data['content']['task_status_id']==6) {
        document.querySelector(`.task-card-item[data-itemId="${data['content']['id']}"]`).remove()  
      }
    } else if (data.type == 'change_profile_amount') {
      
      profile_now = data.content
      active_item = document.querySelector('.task-card-item[data-category-id="3"]');
      active_input = active_item.querySelector('.right-side__current-quantity__amount').value = profile_now;
    }

  };
    
    

};
 // 1. Первоначальный сбор всех данных по WSGI
 // 2. Пока страница открыта, открывается соединение по вебсоккету
 // 3.  Отслеживание событий в реальном времени:
 // - Новое задание (добавить на страницу новое задание)
 // - должны быть функции: добавить новую карточку задания, удалить карточку задания, одновить статус карточки
 // - Изменение статуса заданий (должно быть оповещение)
 //  
})

// Передача видео через websocket (Необходимо раскомментить, как только подключу камеру!)

$(document).ready(function() {
  let list_task = document.querySelectorAll('.task-card-item[data-category="Выполняется"]')
  for (const elem in list_task) {
    if (Object.prototype.hasOwnProperty.call(list_task, elem)) {
      const task = list_task[elem];
      let task_id = task.dataset.itemid
      if (task.dataset.video == 'True') {
          videoStream(task_id)  
      } else {
        alert('Автоматическое определение количества профиля для текущего типа недоступно. Пожалуйста, добавляйте вручную')
      }   
      
    }
  }
})

//Видео поток
const enabled_task = document.querySelector('div.task-card-item[data-category-id="3"]')
let videoElement 
let remoteVideoElement 
let callButton
let hangupButton
let localStream;
let peerConnection;

const serverUrl = 'ws://192.168.211.1/ws/video/'; // URL WebSocket сервера
// const serverUrl = 'ws://127.0.0.1:8000/ws/video/'; // URL WebSocket сервера
let ws;

if (enabled_task) {
  videoElement = enabled_task.querySelector('#localVideo');
  remoteVideoElement = enabled_task.querySelector('#remoteVideo');
  callButton = enabled_task.querySelector('#callButton');
  hangupButton = enabled_task.querySelector('#hangupButton');
  checkboxAutoVision = enabled_task.querySelector('#automatic-vision-checkbox'); 
}



async function videoStream() {
  if (checkboxAutoVision.checked) {
      alert('В данный момент осуществляется автоматическое определение количества профиля');
  } else {
      return;
  }
  console.log('Start Camera button clicked');
  try {
    console.log('Requesting camera access...');
    
    try {
      localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      console.log('Camera access granted, setting video source');
      videoElement.srcObject = localStream;
      callButton.disabled = false;
      callButton.click();
      // startButton.disabled = true;
      console.log('Camera started successfully');
    } catch (cameraError) {
      console.log('Camera not available, creating synthetic video stream');
      
      // Create synthetic video stream for testing
      const canvas = document.createElement('canvas');
      canvas.width = 320;
      canvas.height = 240;
      const ctx = canvas.getContext('2d');
      
      // Create a synthetic video stream
      const stream = canvas.captureStream(30); // 30 FPS
      
      // Animate the canvas
      let frame = 0;
      const animate = () => {
        // Clear canvas
        ctx.fillStyle = '#000080';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw moving rectangle
        const x = (Math.sin(frame * 0.02) * 200) + 220;
        const y = (Math.cos(frame * 0.03) * 150) + 165;
        
        ctx.fillStyle = '#FF0000';
        ctx.fillRect(x, y, 100, 50);
        
        // Draw text
        ctx.fillStyle = '#FFFFFF';
        ctx.font = '20px Arial';
        ctx.fillText(`Test Video Frame: ${frame}`, 50, 50);
        ctx.fillText('Synthetic Camera Feed', 50, 80);
        
        frame++;
        requestAnimationFrame(animate);
        
      };
      
      animate();
      
      localStream = stream;
      // videoElement.srcObject = localStream;
      callButton.disabled = false;
      callButton.click();
      // startButton.disabled = true;
      console.log('Synthetic camera started successfully');
    }
  } catch (e) {
    console.error('Error starting video:', e);
    alert('Error starting video: ' + e.message);
  }
};

if (callButton) {
  callButton.onclick = () => {
    callButton.disabled = true;
    hangupButton.disabled = false;

    // Инициализация WebSocket соединения
    ws = new WebSocket(serverUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      // Отправляем предложение SDP на сервер
      createOfferAndSend();
    };
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'answer') {
        // Получаем ответ SDP от сервера и устанавливаем его
        setRemoteDescription(message.sdp);
      } else if (message.type === 'candidate') {
        // Получаем ICE candidate от сервера и добавляем его
        addIceCandidate(message.candidate);
      } else if (message.type === 'detection_result') {
        // Обрабатываем результаты обнаружения объектов
        console.log('Обнаруженные объекты:', message.objects);
        // TODO: Если требуется, то отражаем результаты на странице
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };
}
if (hangupButton) {
  hangupButton.onclick = () => {
    hangup();
  };
}




async function createPeerConnection() {
  // Configure comprehensive ICE servers for maximum compatibility
  const configuration = {
    iceServers: [
      // Google STUN servers
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
      { urls: 'stun:stun2.l.google.com:19302' },
      { urls: 'stun:stun3.l.google.com:19302' },
      { urls: 'stun:stun4.l.google.com:19302' },
      // Additional public STUN servers
      { urls: 'stun:stun.stunprotocol.org:3478' },
      { urls: 'stun:stun.voiparound.com' },
      { urls: 'stun:stun.voipbuster.com' },
      // Free TURN servers for relay (when STUN fails)
      {
        urls: 'turn:openrelay.metered.ca:80',
        username: 'openrelayproject',
        credential: 'openrelayproject'
      },
      {
        urls: 'turn:openrelay.metered.ca:443',
        username: 'openrelayproject',
        credential: 'openrelayproject'
      },
      {
        urls: 'turn:openrelay.metered.ca:443?transport=tcp',
        username: 'openrelayproject',
        credential: 'openrelayproject'
      }
    ]
  };
  
  peerConnection = new RTCPeerConnection(configuration);
  console.log('PeerConnection created with STUN/TURN servers');

  peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
      console.log('Generated ICE candidate:', event.candidate.type, event.candidate.candidate);
        sendIceCandidate(event.candidate);
      // Отправляем ICE candidate на сервер
      
    } else {
      console.log('ICE candidate gathering completed');
    }
  };

  peerConnection.oniceconnectionstatechange = () => {
    console.log('ICE connection state changed to:', peerConnection.iceConnectionState);
    if (peerConnection.iceConnectionState === 'failed') {
      console.error('ICE connection failed - NAT traversal unsuccessful');
    } else if (peerConnection.iceConnectionState === 'connected') {
      console.log('ICE connection established successfully!');
    } else if (peerConnection.iceConnectionState === 'disconnected') {
      console.warn('ICE connection disconnected');
    }
  };

  peerConnection.onicegatheringstatechange = () => {
    console.log('ICE gathering state changed to:', peerConnection.iceGatheringState);
    if (peerConnection.iceGatheringState === 'complete') {
      console.log('All ICE candidates have been gathered');
    }
  };

  peerConnection.onconnectionstatechange = () => {
    console.log('Connection state changed to:', peerConnection.connectionState);
    if (peerConnection.connectionState === 'failed') {
      console.error('Peer connection failed completely');
    } else if (peerConnection.connectionState === 'connected') {
      console.log('Peer connection established successfully!');
    }
  };

  peerConnection.ontrack = (event) => {
    console.log('Received remote track:', event.track.kind);
    if (event.track.kind === 'video') {
      // Display the processed video from server
      // remoteVideoElement.srcObject = event.streams[0];
      profileType = remoteVideoElement.dataset.profiletype
      input_element = enabled_task.querySelector('.right-side__current-quantity__amount')
      remoteVideoElement.innerHTML = `<p>Ведется работа...</p> <p>Тип профиля: ${profileType}</p><p>Для отмены снимите галочку с поля "Включить автоматическое распознование"</p>`
      console.log('Remote video stream set');
    }
  };

  localStream.getTracks().forEach(track => {
    peerConnection.addTrack(track, localStream);
  });
}

async function createOfferAndSend() {
  await createPeerConnection();
  try {
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    // Отправляем предложение SDP на сервер через WebSocket
    ws.send(JSON.stringify({ type: 'offer', sdp: offer.sdp, task_id: enabled_task.dataset.itemid }));
  } catch (e) {
    console.error('createOffer error:', e);
  }
}

async function setRemoteDescription(sdp) {
  try {
    remote_answer = {type: 'answer', sdp: sdp}
    await peerConnection.setRemoteDescription(remote_answer);
    // ws.send(JSON.stringify(remote_answer))
  } catch (e) {
    console.error('setRemoteDescription error:', e);
  }
}

async function addIceCandidate(candidate) {
  try {
    await peerConnection.addIceCandidate(candidate);
  } catch (e) {
    console.error('addIceCandidate error:', e);
  }
}

function sendIceCandidate(candidate) {
  candidate_new = {
    'candidate': candidate.candidate,
    'foundation': candidate.foundation,
    'ip': candidate.address || candidate.ip,
    'port': candidate.port,
    'protocol': candidate.protocol,
    'type': candidate.type,
    'priority': candidate.priority,
    'component': candidate.component,
    'sdpMid': candidate.sdpMid,
    'sdpMLineIndex': candidate.sdpMLineIndex,
    'tcpType': candidate.tcpType
  }
  ws.send(JSON.stringify({ type: 'candidate', candidate: candidate_new}));
}

function hangup() {
  if (peerConnection) {
    peerConnection.close();
    peerConnection = null;
  }
  if (localStream) {
    localStream.getTracks().forEach(track => track.stop());
    localStream = null;
  }
  if (ws) {
    ws.close();
    ws = null;
  }
  callButton.disabled = false;
  hangupButton.disabled = true;
  startButton.disabled = false;
}


// Работа чекбокса "включить автоматическое распознование"

$(document).ready(function() {

  const auto_vision_checkbox = document.querySelectorAll('#automatic-vision-checkbox[data-statusId="3"]');
  // console.log(auto_vision_checkbox)
  
  for (checkbox of auto_vision_checkbox) {
    input_profile_amount = document.querySelector('.task-card-item[data-category-id="3"]').querySelector('.right-side__current-quantity__amount')
    if (checkbox) {
      if (checkbox.checked) {
        input_profile_amount.disabled = true
        callButton.click();
      } else {
        input_profile_amount.disabled = false
        hangupButton.click();
        remoteVideoElement.innerHTML = `<p>Автоматическая фиксация выключена....</p> <p>Количество изготовленного профиля нужно вводить самостоятельно</p><p>Для старта автоматической фиксации поставьте галочку в поле "Включить автоматическое распознование"</p>`
        }
      checkbox.addEventListener('change', (event)=> {
        if (!checkbox.checked) {
          remoteVideoElement.innerHTML = `<p>Автоматическая фиксация выключена....</p> <p>Количество изготовленного профиля нужно вводить самостоятельно</p><p>Для старта автоматической фиксации поставьте галочку в поле "Включить автоматическое распознование"</p>`
          hangupButton.click(); 
        }

        task_id = document.querySelector('.task-card-item[data-category-id="3"]').dataset.itemid
        fetch(`/change-task-automatic-vision/${task_id}/${checkbox.checked}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
          })
          .then(response=>{
            response.json()
          })
          .then(data=> {
            console.log(data)
          })
        if (checkbox.checked) {
          input_profile_amount.disabled = true
          location.reload();
          
        } else {
          input_profile_amount.disabled = false
        }
      });

    } else {
      console.warn('Element with id "automatic-vision-checkbox" not found');
    }
  }
});
