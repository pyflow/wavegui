from starlette.websockets import WebSocket
import sys
import socket
from contextlib import closing
import uvicorn
import os
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, HTMLResponse, FileResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles
import importlib.resources

_localhost = '127.0.0.1'

def _scan_free_port(port: int = 8000):
    while True:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((_localhost, port)):
                return port
        port += 1


class WaveApp():
    def __init__(self):
        self._routes = []
        self._app = None
        self._startup = []

        with importlib.resources.path('wavegui', '__init__.py') as f:
            self._www_dir = os.path.join(os.path.dirname(f), 'www')
            self._static_dir = os.path.join(self._www_dir, 'static')


    def init_routes(self):
        routes = [
            Route('/', self.homepage),
            WebSocketRoute('/_s', self.handle_ws),
            Mount('/static', StaticFiles(directory=self._static_dir)),
            Route('/{filename}', self.home_file),
        ]
        self._routes = routes

    def init_app(self):
        self._app = Starlette(debug=True, routes=self._routes, on_startup=self._startup)

    def homepage(self, request):
        with open(os.path.join(self._www_dir, 'index.html'), 'r') as f:
            return HTMLResponse(f.read())

    def home_file(self, request):
        name = request.path_params['filename']
        return FileResponse(os.path.join(self._www_dir, name))

    async def handle_ws(self, websocket):
        await websocket.accept()
        while True:
            text = await websocket.receive_text()
            print("get websocket request:", text)
            await websocket.send_text('{"m":{"u":"anon","e":false}}')
            await websocket.send_text('{"e":"not_found"}')

    async def __call__(self, scope, receive, send):
        return await self._app(scope, receive, send)

    def run(self, no_reload=True):
        port = _scan_free_port()
        sys.path.insert(0, '.')
        addr = f'http://{_localhost}:{port}'
        self.init_routes()
        self.init_app()
        uvicorn.run(self, host=_localhost, port=port, reload=not no_reload)
