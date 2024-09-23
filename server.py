import http.server
import socketserver
import os
import urllib.parse
import cgi
from datetime import datetime
import threading
import queue
import time
import socket
import json
import http.client

UPLOAD_FOLDER = 'uploads'
PORT = 12345
TARGET_HOST = 'localhost'
TARGET_PORT = 11434

chat_messages = []
connected_clients = set()
last_message_id = 0
message_lock = threading.Lock()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def fetch_models():
    conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT)
    conn.request('GET', '/api/tags')
    response = conn.getresponse()
    data = response.read().decode()
    conn.close()

    try:
        response_json = json.loads(data)
        model_names = [model['name'] for model in response_json['models']]
        return model_names
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing JSON: {e}")

def generate_response(model_name, prompt):
    request_data = json.dumps({'model': model_name, 'prompt': prompt})
    conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT)
    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(request_data))
    }
    conn.request('POST', '/api/generate', body=request_data, headers=headers)
    response = conn.getresponse()

    data = ''
    full_response = ''
    while chunk := response.read(1024):
        data += chunk.decode()
        boundary = data.rfind('}')
        if boundary != -1:
            json_string = data[:boundary + 1]
            data = data[boundary + 1:]
            for json_str in json_string.split('\n'):
                if json_str.strip():
                    try:
                        response_json = json.loads(json_str)
                        full_response += response_json.get('response', '')
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON: {e}")
    conn.close()
    return full_response.strip()

class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UPLOAD_FOLDER, **kwargs)

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == '/list-files':
            self.list_files()
        elif self.path.startswith('/download/'):
            self.download_file(self.path[10:])
        elif self.path.startswith('/chat'):
            self.handle_chat()
        elif self.path == '/api/models':
            self.handle_models()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/upload':
            self.upload_file()
        elif self.path == '/send-message':
            self.send_message()
        elif self.path == '/api/generate':
            self.handle_generate()
        else:
            self.send_error(404, 'Not Found')

    def list_files(self):
        files = os.listdir(UPLOAD_FOLDER)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"files": files}).encode())

    def download_file(self, filename):
        filename = urllib.parse.unquote(filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            self.send_error(404, 'File not found')
            return

        try:
            with open(file_path, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(file.read())
        except Exception as e:
            self.send_error(500, f"Error sending file: {str(e)}")

    def upload_file(self):
        if 'content-type' not in self.headers:
            self.send_error(400, "Content-Type header doesn't exist")
            return

        content_type = self.headers['content-type']
        if not content_type.startswith('multipart/form-data'):
            self.send_error(400, 'Content-Type must be multipart/form-data')
            return

        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type}
            )

            if 'file' not in form:
                self.send_error(400, 'No file part')
                return

            file_item = form['file']
            if not file_item.filename:
                self.send_error(400, 'No selected file')
                return

            file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(file_item.filename))
            with open(file_path, 'wb') as f:
                f.write(file_item.file.read())

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"message": "File uploaded successfully"}).encode())
        except Exception as e:
            self.send_error(500, f"Error during file upload: {str(e)}")

    def handle_chat(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/event-stream')
        self.send_cors_headers()
        self.end_headers()

        client_id = self.client_address[0]
        last_id = int(self.path.split('=')[-1]) if '=' in self.path else -1

        with message_lock:
            missed_messages = [msg for msg in chat_messages if msg['id'] > last_id]
            for msg in missed_messages:
                self.wfile.write(f"id: {msg['id']}\ndata: {json.dumps(msg, default=str)}\n\n".encode())
            self.wfile.flush()

        connected_clients.add(self)

        try:
            while True:
                time.sleep(1)
                self.wfile.write(b":\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            connected_clients.remove(self)

    def send_message(self):
        global last_message_id
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        message_data = json.loads(post_data.decode('utf-8'))

        username = message_data.get('username', 'Anonymous')
        message = message_data.get('message', '')

        with message_lock:
            last_message_id += 1
            chat_message = {
                'id': last_message_id,
                'username': username,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            chat_messages.append(chat_message)

            for client in connected_clients:
                try:
                    client.wfile.write(f"id: {chat_message['id']}\ndata: {json.dumps(chat_message)}\n\n".encode())
                    client.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    connected_clients.remove(client)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"status": "Message sent", "id": last_message_id}).encode())

    def handle_models(self):
        try:
            models = fetch_models()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'models': models}).encode())
        except Exception as e:
            self.send_error(500, f"Error fetching models: {str(e)}")

    def handle_generate(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode())
            model_name = data['model']
            prompt = data['prompt']
            response = generate_response(model_name, prompt)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'response': response}).encode())
        except Exception as e:
            self.send_error(500, f"Error generating response: {str(e)}")

def run_server():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    IP = get_ip()

    with socketserver.ThreadingTCPServer((IP, PORT), ChatHandler) as httpd:
        print(f"Server running on: {IP}:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
