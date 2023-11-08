from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
KEEP_ALIVE_INTERVAL = 30

online_users = {}

@socketio.on('connect')
def connect():
    sid = request.sid
    socketio.start_background_task(send_keep_alive, sid)

@socketio.on('handshakes')
def handshakes(data):
    data = json.loads(data)
    user_name = data['name']
    online_users[request.sid] = user_name
    join_room(user_name)
    for i in online_users.keys():
        socketio.emit('handshake_revert', list(online_users.values()), room=i)

@socketio.on('message')
def handle_message(data):
    data = json.loads(data)
    recipient_name = data['name']
    if recipient_name=="*all*":
        recipient_sid = get_sid_by_user_name(data['from'])
        for i in online_users.keys():
            if i!=recipient_sid:
                socketio.emit('receive_message_all', [data['from'].split('*#*')[0],data['message']], room=i)
    else:
        recipient_sid = get_sid_by_user_name(recipient_name)
        if recipient_sid:
            socketio.emit('receive_message', [data['from'].split('*#*')[0],data['message']], room=recipient_sid)

@socketio.on('disconnect')
def disconnect():
    user_name = online_users.pop(request.sid, None)
    if user_name:
        print('User Disconnected: ', user_name)
        for i in online_users.keys():
            socketio.emit('handshake_revert', list(online_users.values()), room=i)

def get_sid_by_user_name(user_name):
    for sid, name in online_users.items():
        if name == user_name:
            return sid
    return None

def send_keep_alive(sid):
    while True:
        socketio.emit('ping', room=sid)
        socketio.sleep(KEEP_ALIVE_INTERVAL)

if __name__ == '__main__':
    print('Started')
    socketio.run(app, host='0.0.0.0', port=51223)
