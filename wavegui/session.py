
import logging
from typing import List, Dict, Union, Tuple, Any, Tuple, Callable, Awaitable, Optional
import asyncio
from concurrent.futures import Executor
import string
import random
from datetime import datetime
from .core import PageBase, Expando

try:
    import contextvars  # Python 3.7+ only.
except ImportError:
    contextvars = None

import logging
import functools

logger = logging.getLogger(__name__)


class AsyncPage(PageBase):

    def __init__(self, container, url: str):
        self.container = container
        self._queue = asyncio.Queue(maxsize=1000)
        self._lock = asyncio.Lock()
        super().__init__(url)

    async def save(self):
        """
        """
        p = self._diff()
        if p:
            logger.debug(p)
            await self._patch(p)

    def _make_card(self, data, buf):
        return {'d':data}

    async def _patch(self, ops):
        async with self._lock:
            for op in ops.get('d', []):
                if 'k' in op:
                    if len(op['k']) > 0 and 'd' in op:
                        self.data[op['k']] = self._make_card(op['d'], op.get('b', []))
                else:
                    self.container.pop(self.url, None)

            await self._queue.put(ops)

    async def start_sync(self):
        async with self._lock:
            page_data = self.data;
            self._queue = asyncio.Queue(maxsize=1000)
            return {'p':{'c':page_data}}

    async def changes(self):
        return await self._queue.get()

def random_id(prefix="", length=12):
    assert len(prefix) == 2
    raw_id = ''.join([random.choice('23456789' + string.ascii_uppercase) for i in range(length)])
    return f"{prefix}{raw_id}"

class Session:
    _stores = {}
    @classmethod
    def get(cls, session_id):
        if session_id not in cls._stores:
            store = cls(session_id)
            cls._stores[session_id] = store
        return cls._stores[session_id]

    def __init__(self, session_id=None):
        self.session_id = session_id or random_id('CS', 16)
        self.session_start = datetime.now()
        self.pages = {}

    def page(self, route):
        if route not in self.pages:
            self.pages[route] = AsyncPage(self.pages, route)
        return self.pages[route]

class User:
    def __init__(self, user_id=None, user_name="anon"):
        self.user_id = user_id or 'CU{}'.format('X'*14)
        self.user_name = user_name


class Query:
    """
    Represents the query context.
    The query context is passed to the `@app` handler function whenever a query
    arrives from the browser (page load, user interaction events, etc.).
    """

    def __init__(
            self,
            user: User,
            session: Session,
            route: str,
            args: Expando,
            events: Expando,
            task_manager
    ):
        self.mode = "unicast"
        self.page = session.page(route)
        self.args = args
        self.events = events
        self.user = user
        self.route = route
        self.session = session
        self.task_manager = task_manager

    async def sleep(self, delay: float, result=None) -> Any:
        """
        Suspend execution for the specified number of seconds.
        Always use `q.sleep()` instead of `time.sleep()` in Wave apps.

        Args:
            delay: Number of seconds to sleep.
            result: Result to return after delay, if any.

        Returns:
            The `result` argument, if any, as is.
        """
        return await asyncio.sleep(delay, result)

    async def exec(self, executor: Optional[Executor], func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function in the background using the specified executor.

        To execute a function in-process, use `q.run()`.

        Args:
            executor: The executor to be used. If None, executes the function in-process.
            func: The function to to be called.
            args: Arguments to be passed to the function.
            kwargs: Keywords arguments to be passed to the function.
        Returns:
            The result of the function call.
        """
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)

        loop = asyncio.get_event_loop()

        if contextvars is not None:  # Python 3.7+ only.
            return await loop.run_in_executor(
                executor,
                contextvars.copy_context().run,
                functools.partial(func, *args, **kwargs)
            )

        if kwargs:
            return await loop.run_in_executor(executor, functools.partial(func, *args, **kwargs))

        return await loop.run_in_executor(executor, func, *args)

    async def run(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function in the background, in-process.

        Equivalent to calling `q.exec()` without an executor.

        Args:
            func: The function to to be called.
            args: Arguments to be passed to the function.
            kwargs: Keywords arguments to be passed to the function.

        Returns:
            The result of the function call.
        """
        return await self.exec(None, func, *args, **kwargs)

    async def run_in_back(self, coro) -> Any:
        return await self.task_manager.spawn(coro)