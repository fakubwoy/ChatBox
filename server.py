import socket
import threading
import struct
import json
from datetime import datetime
import base64
import hashlib

SERVER_PORT = 8765
clients = {}
usernames = {}

def send_message(client_socket, message):
    length = len(message)
    if length <= 125:
        client_socket.send(bytes([0x81, length]) + message.encode())
    elif length <= 65535:
        client_socket.send(bytes([0x81, 126]) + struct.pack('>H', length) + message.encode())
    else:
        client_socket.send(bytes([0x81, 127]) + struct.pack('>Q', length) + message.encode())

def receive_message(client_socket):
    try:
        first_byte = client_socket.recv(1)
        if not first_byte:
            return None
        
        second_byte = client_socket.recv(1)
        if not second_byte:
            return None

        length = second_byte[0] & 127

        if length == 126:
            length = struct.unpack('>H', client_socket.recv(2))[0]
        elif length == 127:
            length = struct.unpack('>Q', client_socket.recv(8))[0]

        masks = client_socket.recv(4)
        encoded = client_socket.recv(length)
        decoded = bytearray(length)
        for i in range(length):
            decoded[i] = encoded[i] ^ masks[i % 4]

        return decoded.decode('utf-8')
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None

def broadcast_message(message):
    for client_socket in list(clients.keys()):
        try:
            send_message(client_socket, message)
        except Exception as e:
            print(f"Error sending message: {e}")

def handle_websocket_handshake(client_socket):
    data = client_socket.recv(1024).decode('utf-8')
    headers = {}
    for line in data.split('\r\n')[1:]:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key] = value

    if 'Sec-WebSocket-Key' not in headers:
        return False

    websocket_key = headers['Sec-WebSocket-Key']
    response_key = base64.b64encode(hashlib.sha1((websocket_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()

    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {response_key}\r\n\r\n"
    )

    client_socket.send(response.encode())
    return True

def handle_client(client_socket):
    global usernames

    if not handle_websocket_handshake(client_socket):
        client_socket.close()
        return

    try:
        while True:
            message = receive_message(client_socket)
            if message is None:
                break

            try:
                data = json.loads(message)

                if data['type'] == "SET_USERNAME":
                    if data['username'] in usernames.values():
                        send_message(client_socket, json.dumps({"type": "USERNAME_TAKEN"}))
                    else:
                        clients[client_socket] = data['username']
                        usernames[client_socket] = data['username']
                        send_message(client_socket, json.dumps({"type": "USERNAME_SET", "username": data['username']}))
                        # Notify all clients that a new user has joined
                        broadcast_message(json.dumps({"type": "CHAT", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "username": data['username'], "content": f"{data['username']} has joined the chat"}))
                        print(f"{data['username']} connected: {client_socket.getpeername()}")
                elif data['type'] == "CHAT":
                    sender_username = clients.get(client_socket, 'Anonymous')
                    broadcast_message(json.dumps({"type": "CHAT", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "username": sender_username, "content": data['content']}))
            except json.JSONDecodeError:
                print("Error decoding JSON message.")
            except Exception as e:
                print(f"Error handling message: {e}")
                break

    finally:
        if client_socket in clients:
            username = clients.pop(client_socket, None)
            if username in usernames.values():
                usernames = {key: val for key, val in usernames.items() if val != username}
            print(f"{username} disconnected: {client_socket.getpeername()}")
            broadcast_message(json.dumps({"type": "CHAT", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "username": username, "content": f"{username} has left the chat"}))
        client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', SERVER_PORT))
    server_socket.listen(5)
    ip_address = socket.gethostbyname(socket.gethostname())
    print(f"Server listening on {ip_address}:{SERVER_PORT}")

    while True:
        client_socket, _ = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()
