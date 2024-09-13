# Socket Chat

**Socket Chat** is a simple yet powerful real-time chat application with file sharing, emojis, text formatting, and a responsive user interface. It consists of a Python-based server and a modern web client. No external libraries or installations are required, making it lightweight and easy to set up.

## Key Features

- **Real-time Messaging:** Send and receive messages instantly with a clean, minimalistic interface.
- **File Sharing:** Upload files to the server and download them easily from a file list.
- **Dark Mode Toggle:** Switch between light and dark modes to suit your preference.
- **Responsive Design:** Optimized for all screen sizes, providing a seamless experience on both desktop and mobile devices.
- **Emoji & Text Formatting:** Express yourself with emojis and various text styling options.

## Prerequisites

- **Python 3.x** installed on your system.
- A modern web browser with JavaScript enabled.

## Server Setup

1. **Install Python 3.x:** Ensure Python 3.x is installed and working on your system.
2. **Prepare the Server:**
   - Save the provided server code into a file named `server.py`.
   - Create a folder named `uploads` in the same directory as `server.py`. This will store the files uploaded by users.
3. **Run the Server:**
   - Open a terminal and navigate to the directory where `server.py` is saved.
   - Start the server with the command:
     ```bash
     python server.py
     ```
   - The server will display its IP address and default port (12345). This IP address will be used by clients to connect to the chat.

## Client Setup

1. **Save the Client Files:**
   - Store the provided HTML, CSS, and JavaScript code in a file named `index.html`.
2. **Open the Client:**
   - Open `index.html` in a modern web browser to access the chat interface.

## Usage Instructions

1. **Connect to the Chat:**
   - On the login screen, enter the server's IP address and your chosen username.
   - Click the "Connect" button to join the chat room.

2. **Sending Messages:**
   - Type your message in the input field at the bottom.
   - Use `Enter` to send the message or `Shift+Enter` for multi-line text.
   - Use the text formatting toolbar to style your message with bold, italic, and more.
   - Add emojis to your message using the emoji picker.

3. **File Upload:**
   - Click the "Choose File" button to select a file from your device.
   - Hit "Upload" to send the selected file to the server. Uploaded files will be available for everyone in the chat.

4. **File Download:**
   - Use the file dropdown to browse the list of uploaded files.
   - Select a file and click "Download" to retrieve it.

5. **Dark Mode:**
   - Toggle between dark and light modes using the switch in the top-right corner for better visibility and comfort.

## Additional Notes

- **No External Dependencies:** Socket Chat uses only Python’s inbuilt libraries, eliminating the need for package installations or external libraries (no `pip` required).
- **Browser Compatibility:** Socket Chat works with all major browsers including Chrome, Firefox, and Edge.

