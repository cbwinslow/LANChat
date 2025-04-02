#!/usr/bin/env python3
"""
Name: app.py
Date: 2025-04-02
Purpose: Robust LAN Chat Server with PostgreSQL persistence, global login,
         file exchange, screen sharing, remote control, user presence indicators,
         and notifications.
Function: Runs a Flask application with Socket.IO for real-time communication.
Inputs: HTTP requests, WebSocket messages, file uploads.
Outputs: Chat interface, file downloads, screen sharing & remote control stubs.
Description: This app provides a robust LAN communication system for local use,
             secured with a global username/password login. It uses PostgreSQL for
             chat history and configuration, and includes hooks for screen sharing
             (via WebRTC) and remote control (via noVNC).
File Path: /var/www/chatserver/app.py
"""

import os
import logging
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")
    # Update DATABASE_URL environment variable accordingly, e.g.:
    # export DATABASE_URL="postgresql://username:password@localhost/chatdb"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost/chatdb")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar'}

# -----------------------------------------------------------------------------
# Create and configure the app
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

socketio = SocketIO(app)
db = SQLAlchemy(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Database Models
# -----------------------------------------------------------------------------
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatMessage {self.username}: {self.message}>"

class GlobalConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_password = db.Column(db.String(100), nullable=True)  # Global chat password

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def allowed_file(filename):
    """Check if a file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    """Decorator to enforce login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("You need to log in first.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_global_password():
    """Return the global chat password if set, else None."""
    config = GlobalConfig.query.first()
    return config.chat_password if config else None

def set_global_password(new_pass):
    """Set the global chat password (for the very first user)."""
    config = GlobalConfig.query.first()
    if not config:
        config = GlobalConfig(chat_password=new_pass)
        db.session.add(config)
    else:
        config.chat_password = new_pass
    db.session.commit()

# In-memory set to track online users (socket session ids mapped to usernames)
online_users = {}

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route('/', methods=['GET'])
def home():
    """Redirect to chat if logged in; otherwise, go to login."""
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page: If no global password is set, the first user sets it.
    On POST, the user must provide a username and (if required) the correct password.
    """
    global_password = get_global_password()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username:
            flash("Please enter a valid username.", "error")
            return redirect(url_for('login'))

        # If no global password is set, set it now.
        if not global_password:
            if not password:
                flash("As the first user, please set a chat password.", "error")
                return redirect(url_for('login'))
            set_global_password(password)
            flash("Global chat password set. Welcome!", "success")
        else:
            # Check provided password against stored global password.
            if password != global_password:
                flash("Incorrect chat password.", "error")
                return redirect(url_for('login'))

        session['username'] = username
        flash(f"Welcome, {username}!", "success")
        # Notify others that a new user has joined
        socketio.emit('user_joined', {'username': username}, broadcast=True)
        return redirect(url_for('chat'))
    return render_template('login.html', global_password_set=(global_password is not None))

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    """Logs out the user."""
    username = session.pop('username', None)
    flash("You have been logged out.", "success")
    # Notify others that the user left
    socketio.emit('user_left', {'username': username}, broadcast=True)
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET'])
@login_required
def chat():
    """
    Main chat page.
    Loads chat history and passes online users list.
    Provides options for file upload, screen sharing, and remote control.
    """
    messages = ChatMessage.query.order_by(ChatMessage.timestamp).all()
    return render_template('chat.html', messages=messages, username=session['username'], online_users=list(online_users.values()))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Handle file uploads. Validates file type and saves to uploads folder.
    Notifies chat users of a new file.
    """
    if 'file' not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for('chat'))
    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "error")
        return redirect(url_for('chat'))
    if file and allowed_file(file.filename):
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            flash(f"File '{file.filename}' uploaded successfully.", "success")
            # Notify all clients about the new file upload
            socketio.emit('file_uploaded', {'filename': file.filename, 'username': session['username']}, broadcast=True)
            return redirect(url_for('chat'))
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            flash("File upload failed.", "error")
            return redirect(url_for('chat'))
    else:
        flash("File type not allowed.", "error")
        return redirect(url_for('chat'))

@app.route('/files/<filename>', methods=['GET'])
@login_required
def serve_file(filename):
    """
    Serve a file from the uploads folder.
    """
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        flash("File not found.", "error")
        return redirect(url_for('chat'))

# -----------------------------------------------------------------------------
# Socket.IO Events
# -----------------------------------------------------------------------------
@socketio.on('connect')
def handle_connect():
    """When a socket connects, add user to online list (if logged in)."""
    username = session.get('username')
    if username:
        online_users[request.sid] = username
        emit('update_presence', {'online_users': list(online_users.values())}, broadcast=True)
        logger.info(f"User connected: {username}")
    else:
        # Not logged in: disconnect the socket
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """When a socket disconnects, remove user from online list."""
    username = online_users.pop(request.sid, None)
    if username:
        emit('update_presence', {'online_users': list(online_users.values())}, broadcast=True)
        logger.info(f"User disconnected: {username}")

@socketio.on('send_message')
def handle_send_message(data):
    """
    Handles incoming chat messages.
    Stores the message in PostgreSQL and broadcasts it.
    """
    try:
        username = session.get('username', 'Anonymous')
        message = data.get('message')
        if message:
            chat_msg = ChatMessage(username=username, message=message)
            db.session.add(chat_msg)
            db.session.commit()
            emit('receive_message', {
                'username': username,
                'message': message,
                'timestamp': chat_msg.timestamp.strftime("%H:%M:%S")
            }, broadcast=True)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        emit('error_message', {'error': 'Failed to send message.'})

# -----------------------------------------------------------------------------
# Stub Routes for Screen Sharing & Remote Control
# -----------------------------------------------------------------------------
@app.route('/screenshare', methods=['GET'])
@login_required
def screenshare():
    """
    Stub endpoint for screen sharing.
    For production, integrate WebRTC (or similar) to capture and broadcast the screen.
    """
    return render_template('screenshare.html', username=session['username'])

@app.route('/remotecontrol', methods=['GET'])
@login_required
def remotecontrol():
    """
    Stub endpoint for remote control.
    For full functionality, integrate with a VNC server and noVNC client.
    """
    return render_template('remotecontrol.html', username=session['username'])

# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return render_template('500.html'), 500

# -----------------------------------------------------------------------------
# Main entry
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        # Run on LAN on port 5000; for production, run behind Apache2 reverse proxy if desired.
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
