// script.js
// Handles WebSocket communication, message sending, and presence updates

document.addEventListener('DOMContentLoaded', () => {
  const socket = io();
  const sendBtn = document.getElementById('send-btn');
  const messageInput = document.getElementById('message-input');
  const chatBox = document.getElementById('chat-box');
  const userList = document.getElementById('user-list');

  // Send message on button click or Enter key press
  function sendMessage() {
    const message = messageInput.value.trim();
    if (message) {
      socket.emit('send_message', { message: message });
      messageInput.value = '';
    }
  }

  sendBtn.addEventListener('click', sendMessage);
  messageInput.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });

  // Append a new chat message to the chat box
  socket.on('receive_message', (data) => {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('chat-message');
    msgDiv.innerHTML = `<span class="timestamp">[${data.timestamp}]</span> <strong>${data.username}</strong>: ${data.message}`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  });

  // Update user presence list
  socket.on('update_presence', (data) => {
    userList.textContent = data.online_users.join(', ');
  });

  // Notification for file uploads
  socket.on('file_uploaded', (data) => {
    const notif = document.createElement('div');
    notif.classList.add('chat-message');
    notif.innerHTML = `<em>${data.username} uploaded file: ${data.filename}</em>`;
    chatBox.appendChild(notif);
    chatBox.scrollTop = chatBox.scrollHeight;
  });

  // Handle error messages from the server
  socket.on('error_message', (data) => {
    alert(data.error);
  });
});

