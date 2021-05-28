from starlette.websockets import WebSocket
import sys
import socket
from contextlib import closing
import uvicorn
import click
import os

_localhost = '127.0.0.1'

async def app(scope, receive, send):
    websocket = WebSocket(scope=scope, receive=receive, send=send)
    await websocket.accept()
    await websocket.send_text('Hello, world!')
    await websocket.close()

def _scan_free_port(port: int = 8000):
    while True:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((_localhost, port)):
                return port
        port += 1


def main(no_reload=True):
    port = _scan_free_port()
    addr = f'http://{_localhost}:{port}'
    os.environ['H2O_WAVE_INTERNAL_ADDRESS'] = addr  # TODO deprecated
    os.environ['H2O_WAVE_EXTERNAL_ADDRESS'] = addr  # TODO deprecated
    os.environ['H2O_WAVE_APP_ADDRESS'] = addr

    sys.path.insert(0, '.')

    uvicorn.run(app, host=_localhost, port=port, reload=not no_reload)
