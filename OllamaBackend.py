import http.server
import socketserver
import http.client
import json

PORT = 11435
TARGET_HOST = 'localhost'
TARGET_PORT = 11434

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

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_response_with_cors(self, code, headers=None):
        self.send_response(code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response_with_cors(200)

    def do_GET(self):
        if self.path == '/api/models':
            try:
                models = fetch_models()
                self.send_response_with_cors(200, {'Content-Type': 'application/json'})
                self.wfile.write(json.dumps({'models': models}).encode())
            except Exception as e:
                self.send_response_with_cors(500, {'Content-Type': 'text/plain'})
                self.wfile.write(str(e).encode())
        else:
            self.send_response_with_cors(404, {'Content-Type': 'text/plain'})
            self.wfile.write(b'Not Found')

    def do_POST(self):
        if self.path == '/api/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            try:
                data = json.loads(post_data)
                model_name = data['model']
                prompt = data['prompt']
                response = generate_response(model_name, prompt)
                self.send_response_with_cors(200, {'Content-Type': 'application/json'})
                self.wfile.write(json.dumps({'response': response}).encode())
            except Exception as e:
                self.send_response_with_cors(500, {'Content-Type': 'text/plain'})
                self.wfile.write(str(e).encode())
        else:
            self.send_response_with_cors(404, {'Content-Type': 'text/plain'})
            self.wfile.write(b'Not Found')

def run_server():
    with socketserver.TCPServer(('', PORT), RequestHandler) as httpd:
        print(f"Backend service listening at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == '__main__':
    run_server()
