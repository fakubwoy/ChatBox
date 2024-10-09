import os
import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests

UPLOAD_FOLDER = 'uploads'
PORT = 12345
TARGET_PORT = 11434
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Get the root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Read targetlist file
def read_targetlist():
    targetlist_file = os.path.join(ROOT_DIR, 'targetlist.txt')
    if not os.path.exists(targetlist_file):
        raise Exception("targetlist file not found")
    with open(targetlist_file, 'r') as f:
        targets = [line.strip() for line in f if line.strip()]
    if not targets:
        raise Exception("No targets found in targetlist")
    return targets

TARGET_HOSTS = read_targetlist()

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for chat messages
chat_messages = []
last_message_id = 0
message_lock = threading.Lock()
message_available = threading.Condition()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def fetch_models():
    for host in TARGET_HOSTS:
        url = f'http://{host}:{TARGET_PORT}/api/tags'
        print(url)
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            response_json = response.json()
            model_names = [model['name'] for model in response_json.get('models', [])]
            return model_names
        except (requests.RequestException, json.JSONDecodeError):
            continue  # Try next host
    # If all hosts fail
    raise Exception("Error fetching models: All targets failed")

def generate_response(model_name, prompt):
    for host in TARGET_HOSTS:
        url = f'http://{host}:{TARGET_PORT}/api/generate'
        headers = {'Content-Type': 'application/json'}
        payload = {'model': model_name, 'prompt': prompt}
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            response_json = response.json()
            return response_json.get('response', '').strip()
        except (requests.RequestException, json.JSONDecodeError):
            continue  # Try next host
    # If all hosts fail
    raise Exception("Error generating response: All targets failed")

# Serve index.html
@app.route('/', methods=['GET'])
def index():
    return "hello world"

@app.route('/list-files', methods=['GET'])
def list_files():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        return jsonify({"files": files}), 200
    except Exception as e:
        return jsonify({"error": f"Error listing files: {e}"}), 500

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error sending file: {e}"}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # Check if filename exists and is allowed
    if not file or not file.filename:
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    if not allowed_file(filename):
        return jsonify({"error": "File type not allowed"}), 400

    try:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": "File uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error during file upload: {e}"}), 500

@app.route('/chat', methods=['GET'])
def handle_chat():
    def event_stream(last_id):
        while True:
            with message_available:
                notified = message_available.wait(timeout=15)
                if notified:
                    with message_lock:
                        missed_messages = [msg for msg in chat_messages if msg['id'] > last_id]
                        for msg in missed_messages:
                            yield f"id: {msg['id']}\ndata: {json.dumps(msg)}\n\n"
                            last_id = msg['id']
                else:
                    # Send a keep-alive comment
                    yield ": keep-alive\n\n"

    last_id_str = request.args.get('last_id')
    try:
        last_id = int(last_id_str) if last_id_str is not None else -1
    except ValueError:
        last_id = -1  # Default value if conversion fails

    return Response(stream_with_context(event_stream(last_id)),
                    mimetype='text/event-stream')

@app.route('/send-message', methods=['POST'])
def send_message():
    global last_message_id
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get('username', 'Anonymous')
    message = data.get('message', '')

    with message_lock:
        last_message_id += 1
        chat_message = {
            'id': last_message_id,
            'username': username,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        chat_messages.append(chat_message)

    with message_available:
        message_available.notify_all()

    return jsonify({"status": "Message sent", "id": last_message_id}), 200

@app.route('/api/models', methods=['GET'])
def api_models():
    try:
        models = fetch_models()
        return jsonify({'models': models}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching models: {e}"}), 500

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    model_name = data.get('model')
    prompt = data.get('prompt')

    if not model_name or not prompt:
        return jsonify({"error": "Model name and prompt are required"}), 400

    try:
        response = generate_response(model_name, prompt)
        return jsonify({'response': response}), 200
    except Exception as e:
        return jsonify({"error": f"Error generating response: {e}"}), 500

def run_server():
    from waitress import serve
    serve(app, host='0.0.0.0', port=PORT)
#command to run
# waitress-serve --port=12345 guniserver:app
if __name__ == "__main__":
    run_server()