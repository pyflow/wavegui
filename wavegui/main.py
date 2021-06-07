from typing import Dict, Tuple, Callable, Any, Awaitable, Optional
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
import traceback
import logging
import json
import asyncio
from .core import Query, UNICAST, Expando, random_id, Session, User
from .ui import markdown_card
from datetime import datetime
from .exception import NoHandlerException

HandleAsync = Callable[[Query], Awaitable[Any]]

_localhost = '127.0.0.1'

logger = logging.getLogger(__name__)

def _scan_free_port(port: int = 8000):
    while True:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((_localhost, port)):
                return port
        port += 1


class ClientRequest:
    bad_request = object()
    invalid_request = object()
    action_map = {
        '*': 'patch',
        '@': 'query',
        '+': 'watch',
        '#': 'noop'
    }
    @classmethod
    def load(cls, client, msg):
        parts = msg.split(' ', 3)
        if len(parts) != 3:
            return cls.bad_request
        t, addr, data = parts[0], parts[1], parts[2]
        action = cls.action_map.get(t, None)
        if not action:
            return cls.invalid_request
        return cls(client, action, str(addr), data)

    def __init__(self, client, action, addr, data):
        assert action in self.action_map.values()
        self.action = action
        self.addr = addr
        self.data = data
        self.client = client

    def json(self):
        if not self.data:
            return {}
        return json.loads(self.data)

    async def send_text(self, text):
        await self.websocket.send_text(text)


class WaveClient:
    def __init__(self, websocket, app):
        self.websocket = websocket
        self.app = app
        self.q = None
        self.sync_task = None
        self.quit = False
        self.user = None
        self.session = None
        self.page_route = None

    async def handle(self):
        websocket = self.websocket
        await websocket.accept()
        while not self.quit:
            text = await websocket.receive_text()
            req = ClientRequest.load(self, text)
            if req in [ClientRequest.invalid_request, ClientRequest.bad_request, None]:
                continue
            print('client request:', req.action, req.addr, req.data)
            await self.process(req)
            if req.action == 'watch':
                self.page_route = req.addr
            if self.q != None and self.sync_task == None and self.page_route != None:
                self.sync_task = asyncio.create_task(self.page_sync())
            #await websocket.send_text('{"m":{"u":"anon","e":false}}')

    async def page_sync(self):
        assert self.q != None
        page = self.session.page(self.page_route)
        page_data = await page.start_sync()
        if page_data:
            await self.websocket.send_text(json.dumps(page_data))
        while not self.quit:
            data = await page.changes()
            await self.websocket.send_text(json.dumps(data))

    async def process(self, req):
        args = req.json()
        events_state: Optional[dict] = args.get('', None)
        self.session = Session()
        self.user = User()
        q = Query(
            session = self.session,
            user = self.user,
            route = req.addr,
            args = Expando(args),
            events = Expando(events_state),
        )
        self.q = q
        # noinspection PyBroadException,PyPep8
        try:
            await self.app.handle(req.addr, q)
        except NoHandlerException:
            await self.websocket.send_text('{"e":"not_found"}')
        except:
            logger.exception('Unhandled exception')
            # noinspection PyBroadException,PyPep8
            try:
                q.page.drop()
                # TODO replace this with a custom-designed error display
                q.page['__unhandled_error__'] = markdown_card(
                    box='1 1 12 10',
                    title='Error',
                    content=f'```\n{traceback.format_exc()}\n```',
                )
                await q.page.save()
            except:
                logger.exception('Failed transmitting unhandled exception')

class WaveApp:
    def __init__(self):
        self._mode = None
        self._base_url = ''
        self._routes = {}
        self._startup = []
        self._shutdown = []


    def setup(self, route, handle, mode=None, on_startup=None, on_shutdown=None):
        self.mode = mode or UNICAST
        self._routes[route] = handle
        WaveServer.register(self)

    def run(self, no_reload=True):
        WaveServer.run(no_reload=no_reload)

    async def handle(self, route, q):
        handler = self._routes.get(route)
        if handler == None:
            raise NoHandlerException(f'No handler for {route} registered.')
        await handler(q)


    def __call__(self, route: str, mode=None, on_startup: Optional[Callable] = None,
            on_shutdown: Optional[Callable] = None):

        def wrap(handle: HandleAsync):
            self.setup(route, handle, mode, on_startup, on_shutdown)
            return handle

        return wrap


class WaveServer:
    _server = None
    _apps = []

    @classmethod
    def run(cls, no_reload=True):
        if not cls._server:
            cls._server = cls()
        cls._server.run_forever(no_reload=no_reload)

    @classmethod
    def register(cls, app):
        if app not in cls._apps:
            cls._apps.append(app)


    def __init__(self):
        self._routes = []
        self._server = None
        self._startup = []

        with importlib.resources.path('wavegui', '__init__.py') as f:
            self._www_dir = os.path.join(os.path.dirname(f), 'www')
            self._static_dir = os.path.join(self._www_dir, 'static')


    def init_routes(self):
        routes = []
        for app in self._apps:
            for route in app._routes:
                routes.append(Route(route, self.homepage))
        routes.extend([
            Route('/', self.homepage),
            WebSocketRoute('/_s', self.handle_ws),
            Mount('/static', StaticFiles(directory=self._static_dir)),
            Route('/{filename}', self.home_file)
            ])
        self._routes = routes

    def init_server(self):
        self._server = Starlette(debug=True, routes=self._routes, on_startup=self._startup)

    def homepage(self, request):
        with open(os.path.join(self._www_dir, 'index.html'), 'r') as f:
            return HTMLResponse(f.read())

    def home_file(self, request):
        name = request.path_params['filename']
        return FileResponse(os.path.join(self._www_dir, name))

    async def handle_ws(self, websocket):
        client = WaveClient(websocket, self._apps[0])
        await client.handle()

    async def __call__(self, scope, receive, send):
        return await self._server(scope, receive, send)

    def run_forever(self, no_reload=True):
        port = _scan_free_port()
        sys.path.insert(0, '.')
        addr = f'http://{_localhost}:{port}'
        self.init_routes()
        self.init_server()
        uvicorn.run(self, host=_localhost, port=port, reload=not no_reload)
