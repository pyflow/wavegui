from starlette.websockets import WebSocket
import sys
import socket
from contextlib import closing
import uvicorn
import os

_localhost = '127.0.0.1'

def _scan_free_port(port: int = 8000):
    while True:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((_localhost, port)):
                return port
        port += 1


class WaveApp():
    def __init__(self):
        pass

    async def __call__(self, scope, receive, send):
        websocket = WebSocket(scope=scope, receive=receive, send=send)
        await websocket.accept()
        await websocket.send_text('Hello, world!')
        await websocket.close()

    def run(self, no_reload=True):
        port = _scan_free_port()
        addr = f'http://{_localhost}:{port}'

        sys.path.insert(0, '.')

        uvicorn.run(self, host=_localhost, port=port, reload=not no_reload)
