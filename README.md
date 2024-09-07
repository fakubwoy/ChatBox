# Socket Chat

Socket Chat is a simple real-time chat application built using WebSockets. It provides a clean, modern interface with chat bubbles for user messages. Sent messages are displayed on the right, and received messages are shown on the left. The application also supports real-time user communication and includes message timestamps and usernames inside the chat bubbles.

## Features
- **Real-time communication** using WebSockets.
- **Chat bubbles**: Sent messages are displayed on the right, received messages on the left.
- **Responsive design**: The chat window adapts to the size of the screen.
- **Username prompt**: Users are prompted to enter a unique username on connection.
- **Keyboard shortcuts**: Press `Enter` to send a message and `Shift+Enter` to insert a new line.
- **Message timestamps**: Each message includes a timestamp within the chat bubble.

## File Transfer (In Progress)
In addition to chat functionality, **Socket Chat** is being enhanced to support file transfers between clients. The goal is to allow users to upload and download files through the chat interface.

### Planned File Transfer Features
- **Send files**: Users can upload files to the chat, and other users can download them.
- **Progress tracking**: Show file transfer progress in real-time.
- **Seamless integration**: Files will appear as clickable links or thumbnails within the chat window.

*This feature is still under development.*

## How to Run
1. Clone the repository:
    ```bash
    git clone https://github.com/fakubwoy/Socket-Chat.git
    ```
2. Start the WebSocket server on your local machine:
    ```bash
    python server.py
    ```
3. Open the `index.html` file in your browser to start chatting!

## Requirements
- Python 3.x
