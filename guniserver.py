import os
import urllib.parse
import json
import http.client
from datetime import datetime
import threading
import time
import socket
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
import gunicorn.app.base
from queue import Queue, Empty

UPLOAD_FOLDER = 'uploads'
PORT = 12345
TARGET_HOST = 'localhost'
TARGET_PORT = 11434

chat_messages = []
last_message_id = 0
message_lock = threading.Lock()
message_queue = Queue()

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

@app.route('/list-files', methods=['GET'])
def list_files():
    files = os.listdir(UPLOAD_FOLDER)
    return jsonify({"files": files})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": "File uploaded successfully"})

@app.route('/chat')
def chat():
    def generate():
        last_id = int(request.args.get('last_id', -1))

        with message_lock:
            missed_messages = [msg for msg in chat_messages if msg['id'] > last_id]
            for msg in missed_messages:
                yield f"data: {json.dumps(msg, default=str)}\n\n"

        while True:
            try:
                message = message_queue.get(timeout=20)
                yield f"data: {json.dumps(message, default=str)}\n\n"
            except Empty:
                yield ": keepalive\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

@app.route('/send-message', methods=['POST'])
def send_message():
    global last_message_id
    data = request.json
    username = data.get('username', 'Anonymous')
    message = data.get('message', '')

    with message_lock:
        last_message_id += 1
        chat_message = {
            'id': last_message_id,
            'username': username,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        chat_messages.append(chat_message)
        message_queue.put(chat_message)

    return jsonify({"status": "Message sent", "id": last_message_id})

@app.route('/api/models', methods=['GET'])
def handle_models():
    try:
        models = fetch_models()
        return jsonify({'models': models})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def handle_generate():
    data = request.json
    model_name = data['model']
    prompt = data['prompt']
    try:
        response = generate_response(model_name, prompt)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    IP = get_ip()

    options = {
        'bind': f'{IP}:{PORT}',
        'workers': 1, 
        'worker_class': 'gevent',
    }
    StandaloneApplication(app, options).run()
