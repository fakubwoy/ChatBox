# Socket Chat

Socket Chat is a simple, real-time chat application with file sharing capabilities. It consists of a Python server and a web-based client interface.

## Features

- Real-time messaging
- File upload and download functionality
- Dark mode toggle
- Responsive design

## Prerequisites

- Python 3.x
- Modern web browser with JavaScript enabled

## Server Setup

1. Ensure you have Python 3.x installed on your system.
2. Save the server code in a file named `server.py`.
3. Create a directory named `uploads` in the same location as `server.py`.
4. Run the server using the command:
   ```
   python server.py
   ```
5. The server will start and display its IP address and port (default: 12345).

## Client Setup

1. Save the HTML/CSS/JavaScript code in a file named `index.html`.
2. Open `index.html` in a web browser.

## Usage

1. On the login screen, enter the server's IP address and your desired username.
2. Click "Connect" to join the chat.
3. Use the message input field to send messages.
4. To upload a file:
   - Click "Choose File" to select a file from your device.
   - Click "Upload" to send the file to the server.
5. To download a file:
   - Select a file from the dropdown list.
   - Click "Download" to retrieve the file from the server.
6. Toggle dark mode using the switch in the top-right corner.
