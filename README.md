README.md

# Hacker Chat Server

A lightweight LAN chat server with a hacker theme, built using Flask, Flask-SocketIO, and SQLite. This project features a global login system, persistent chat history, file exchange, and stub pages for screen sharing and remote control. It’s designed for easy LAN deployment and can be securely exposed using tools like Cloudflare Tunnel if needed.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

This repo contains a complete LAN chat server application with a “hacker” aesthetic. It is ideal for secure, local communication and file exchange on your LAN. The server uses SQLite to store chat messages and global configuration (like the chat password), and it is built with modularity and robustness in mind.

## Features

- **Global Login:** The first user sets the chat password, and subsequent logins require the correct password.
- **Persistent Chat History:** All messages are stored in a lightweight SQLite database.
- **File Exchange:** Users can easily upload and download files within the LAN.
- **Presence Indicators:** Real-time tracking of online users.
- **Stub Pages:** Placeholders for future integration of screen sharing (via WebRTC) and remote control (via noVNC).
- **Hacker Theme:** A dark, neon-green design that adds a fun “hacker” vibe to the interface.
- **Robust Error Handling:** Logging and error-catching mechanisms ensure smooth operation.

## Prerequisites

- **Python 3.6+** (recommended Python 3.8 or later)
- **pip3** (Python package manager)
- **SQLite** (included with Python’s standard library)
- **Virtual Environment (optional but recommended)**

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/hacker-chat-server.git
   cd hacker-chat-server

    Create and Activate a Virtual Environment (Optional):

python3 -m venv venv
source venv/bin/activate

Install Dependencies:

pip3 install -r requirements.txt

The requirements.txt should include:

Flask
Flask-SocketIO
Flask-SQLAlchemy
eventlet

Directory Setup:

Ensure the following structure exists:

    /var/www/chatserver/
    ├── app.py
    ├── chat.db                 # Automatically created on first run
    ├── uploads/                # Automatically created on first run
    ├── templates/
    │   ├── login.html
    │   ├── chat.html
    │   ├── screenshare.html
    │   ├── remotecontrol.html
    │   ├── 404.html            # Optional
    │   └── 500.html            # Optional
    └── static/
        ├── style.css
        └── script.js

Configuration

    Secret Key: The application uses a default secret key from the environment variable SECRET_KEY. Change it for production.

    Database: The app uses SQLite (chat.db) located in the root folder. It is created automatically if it does not exist.

    Uploads: Files are saved in the uploads/ directory. Allowed file extensions include: txt, pdf, png, jpg, jpeg, gif, zip, rar.

Usage

    Start the Server:

python3 app.py

The server will run on http://<your-local-ip>:5000.

Access the Chat Application:

    Open a web browser and navigate to http://<your-local-ip>:5000.

    On the login page, the first user sets the global chat password. Subsequent users must enter this password.

Features:

    Chat: Send and receive real-time messages.

    File Exchange: Upload files via the provided form and download them by clicking on the links.

    Screen Sharing & Remote Control: Visit the stub pages to see placeholders. Integration with WebRTC and noVNC can be added later.

    Logout: Click the logout link to end your session.

Exposing the Server:

    For secure remote access, you can use Cloudflare Tunnel:

        Install cloudflared and authenticate with your Cloudflare account.

        Run: cloudflared tunnel --url http://localhost:5000 to receive a public URL.
