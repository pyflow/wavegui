import inspect
from typing import Dict, Tuple, Callable, Any, Awaitable, Optional
from starlette.websockets import WebSocket, WebSocketDisconnect
from websockets.exceptions import WebSocketException
import sys
import socket
from contextlib import closing
import uvicorn
import os
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import PlainTextResponse, HTMLResponse, FileResponse, RedirectResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles
import importlib.resources
import traceback
import logging
import json
import asyncio
from asyncio import CancelledError
from .utils import IDGenerator
from .core import UNICAST, Expando
from .session import Query, Session, UserInfo
from .ui import markdown_card
from .exception import NoHandlerException, RouteDuplicatedError, AppNotFoundException
from .task import TaskManager

HandleAsync = Callable[[Query], Awaitable[Any]]

logger = logging.getLogger(__name__)

def _scan_free_port(port: int = 8000):
    _localhost = '127.0.0.1'
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
        try:
            return json.loads(self.data)
        except:
            return {'#': self.data}


class WaveClient:
    def __init__(self, websocket):
        self.websocket = websocket
        self.sync_task = None
        self.quit = False
        self.user_info = UserInfo()
        session_id = websocket.scope.get('session', {}).get('session_id', None) or IDGenerator.create_session_id()
        self.session = Session(session_id=session_id)
        self.page_route = None
        self.task_manager = TaskManager(name=self.session.session_id, pool_size=5)

    async def handle(self):
        websocket = self.websocket
        await websocket.accept()

        while not self.quit:
            try:
                text = await websocket.receive_text()
            except WebSocketDisconnect:
                await self._close_sync_task()
                await self.close()
                return
            except WebSocketException:
                await self._close_sync_task()
                await self.close()
                return

            req = ClientRequest.load(self, text)
            if req in [ClientRequest.invalid_request, ClientRequest.bad_request, None]:
                continue
            if req.action == 'watch':
                self.page_route = req.addr
                await self.task_manager.spawn(self.start_sync_task())

            await self.process(req)

    async def _close_sync_task(self):
        if not self.sync_task:
            return
        try:
            self.sync_task.cancel()
            await asyncio.wait([self.sync_task], timeout=2)
            self.sync_task = None
        except CancelledError:
            pass


    async def start_sync_task(self):
        if self.sync_task != None:
            await self._close_sync_task()
        if self.sync_task == None and self.page_route != None:
            self.sync_task = asyncio.create_task(self.page_sync())

    async def send_text(self, text):
        try:
            await self.websocket.send_text(text)
        except WebSocketException:
            await self.close()
            return
        except WebSocketDisconnect:
            await self.close()
            return

    async def page_sync(self):
        assert self.session != None
        page = self.session.page(self.page_route)
        page_data = await page.start_sync()
        if page_data:
            await self.send_text(json.dumps(page_data))

        while not self.quit:
            data = await page.changes()
            await self.send_text(json.dumps(data))


    async def process(self, req):
        args = req.json()
        events_state: Optional[dict] = args.get('', None)
        q = Query(
            session = self.session,
            user_info = self.user_info,
            route = req.addr,
            args = Expando(args),
            events = Expando(events_state),
            task_manager = self.task_manager
        )
        # noinspection PyBroadException,PyPep8
        try:
            app = WaveApp.get(req.addr)
            await app.handle(req.addr, q)
        except NoHandlerException:
            await self.send_text('{"e":"not_found"}')
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

    async def close(self):
        try:
            self.quit = True
            await self.websocket.close()
        except Exception as ex:
            logger.debug(f'Exception when close, {ex}')

        await self.task_manager.join(timeout=1)

class WaveApp:
    _apps = []
    _app_routes = {}
    _session_config = dict(secret_key="wavegui_secret",
            session_cookie ="wave-session",
            max_age=86400*14, same_site="lax", https_only=False)

    @classmethod
    def register(cls, app):
        if app in cls._apps:
            return
        cls._apps.append(app)
        for route in app._routes:
            if route in cls._app_routes:
                raise RouteDuplicatedError(f'Route {route} duplicated, registered twice.')
            cls._app_routes[route] = app
    
    @classmethod
    def get_middlewares(cls):
        return [Middleware(SessionMiddleware, **cls._session_config)]


    @classmethod
    def all(cls):
        return cls._apps

    @classmethod
    def get(cls, route):
        app = cls._app_routes.get(route, None)
        if app == None:
            raise AppNotFoundException(f'App for {route} not found.')
        return app

    def __init__(self):
        self._mode = None
        self._base_url = ''
        self._routes = {}
        self._startup = []
        self._shutdown = []


    def setup(self, route, handle, mode=None, on_startup=None, on_shutdown=None):
        self.mode = mode or UNICAST
        self._routes[route] = handle
        WaveApp.register(self)
    
    @classmethod
    def config_session(cls, max_age: 86400*14, session_cookie="", secret_key=""):
        cls._session_config['max_age'] = max_age
        if session_cookie:
            cls._session_config['session_cookie'] = session_cookie
        if secret_key:
            cls._session_config['secret_key'] = secret_key

    def run(self, no_reload=True, log_level="info"):
        WaveServer.run(no_reload=no_reload, log_level=log_level)

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

    @classmethod
    def run(cls, no_reload=True, log_level="info"):
        if not cls._server:
            cls._server = cls()
        cls._server.run_forever(no_reload=no_reload, log_level=log_level)


    def __init__(self):
        self._routes = []
        self._server = None
        self._startup = []
        self.default_route = ''

        with importlib.resources.path('wavegui', '__init__.py') as f:
            self._www_dir = os.path.join(os.path.dirname(f), 'www')
            self._static_dir = os.path.join(self._www_dir, 'static')
            self._fonts_dir = os.path.join(self._www_dir, 'fonts')


    def init_routes(self):
        self.default_route = ''
        routes = []
        for app in WaveApp.all():
            for route in app._routes:
                if not self.default_route:
                    self.default_route = route
                routes.append(Route(route, self.app_page))
        routes.extend([
            Route('/', self.homepage),
            WebSocketRoute('/_s/', self.handle_ws),
            Mount('/static', StaticFiles(directory=self._static_dir)),
            Mount('/fonts', StaticFiles(directory=self._fonts_dir)),
            Route('/manifest.json', self.home_file),
            Route('/favicon.ico', self.home_file),
            Route('/logo192.png', self.home_file)
            ])
        self._routes = routes

    def init_server(self):
        middleware = []
        middleware.extend(WaveApp.get_middlewares())
        self._server = Starlette(debug=True, routes=self._routes, middleware=middleware, on_startup=self._startup)

    def homepage(self, request):
        if 'session_id' not in request.session:
           request.session['session_id'] = IDGenerator.create_session_id()
        return RedirectResponse(url=self.default_route)
    
    def app_page(self, request):
        if 'session_id' not in request.session:
           request.session['session_id'] = IDGenerator.create_session_id()
        with open(os.path.join(self._www_dir, 'index.html'), 'r') as f:
            return HTMLResponse(f.read())

    def home_file(self, request):
        name = os.path.basename(request.url.path)
        return FileResponse(os.path.join(self._www_dir, name))

    async def handle_ws(self, websocket):
        client = WaveClient(websocket)
        await client.handle()

    async def __call__(self, scope, receive, send):
        return await self._server(scope, receive, send)

    def run_forever(self, no_reload=True, log_level="info"):
        port = _scan_free_port()
        sys.path.insert(0, '.')
        self.init_routes()
        self.init_server()
        uvicorn.run(self, host='0.0.0.0', port=port, reload=not no_reload, log_level=log_level)
