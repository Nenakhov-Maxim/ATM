const videoElement = document.getElementById('localVideo');
const remoteVideoElement = document.getElementById('remoteVideo');
const startButton = document.getElementById('startButton');
const callButton = document.getElementById('callButton');
const hangupButton = document.getElementById('hangupButton');

let localStream;
let peerConnection;
const serverUrl = 'ws://127.0.0.1:8000/ws/object_detection/'; // URL WebSocket сервера

let ws;
startButton.onclick = async () => {
  console.log('Start Camera button clicked');
  try {
    console.log('Requesting camera access...');
    
    // Try to get real camera first
    try {
      localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      console.log('Camera access granted, setting video source');
      videoElement.srcObject = localStream;
      callButton.disabled = false;
      startButton.disabled = true;
      console.log('Camera started successfully');
    } catch (cameraError) {
      console.log('Camera not available, creating synthetic video stream');
      
      // Create synthetic video stream for testing
      const canvas = document.createElement('canvas');
      canvas.width = 640;
      canvas.height = 480;
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
      videoElement.srcObject = localStream;
      callButton.disabled = false;
      startButton.disabled = true;
      console.log('Synthetic camera started successfully');
    }
  } catch (e) {
    console.error('Error starting video:', e);
    alert('Error starting video: ' + e.message);
  }
};


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
      // TODO: Отобразите результаты на странице (например, наложите рамки на видео)
    }
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
};

hangupButton.onclick = () => {
  hangup();
};

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
      remoteVideoElement.srcObject = event.streams[0];
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
    ws.send(JSON.stringify({ type: 'offer', sdp: offer.sdp }));
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
