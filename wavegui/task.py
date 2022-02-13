
import asyncio
from asyncio import Semaphore
from asyncio import CancelledError
import asyncio
from functools import partial
import inspect
import logging

logger = logging.getLogger(__name__)

class AsyncPool(object):
    def __init__(self, size=10, max_running_time=300):
        self.size = size
        self.max_running_time = max_running_time
        self.waiting = set()
        self.active = set()
        self.semaphore = Semaphore(self.size)


    @property
    def is_empty(self):
        return 0 == len(self.waiting) == len(self.active)

    @property
    def is_full(self):
        return self.size <= len(self.waiting) + len(self.active)

    async def coro_wrap(self, coro, cb=None, ctx=None):
        parent_task = asyncio.current_task()
        task = asyncio.create_task(coro)
        self.waiting.remove(parent_task)
        self.active.add(parent_task)
        try:
            ret = await asyncio.wait_for(task, timeout=self.max_running_time)
            logger.debug("task returned: {ret}.", ret=ret)
        except asyncio.TimeoutError:
            logger.error('timeout')
        except Exception as ex:
            logger.error(f'exception: {ex}')
        finally:
            logger.debug("task completed, will release semaphor.")
            self.semaphore.release()
            self.active.remove(parent_task)

    async def spawn(self, coro, cb=None, ctx=None):
        await self.semaphore.acquire()
        task = asyncio.create_task(self.coro_wrap(coro))
        self.waiting.add(task)

    async def join(self, timeout=3):
        tasks = self.active | self.waiting
        if len(tasks) > 0:
            done, pending = await asyncio.wait(tasks, timeout=timeout)
            waiting = []
            for task in pending:
                try:
                    task.cancel()
                    waiting.append(task)
                except CancelledError:
                    pass
            await asyncio.wait(waiting, timeout=2)



def iscoroutine_or_partial(obj):
    while isinstance(obj, partial):
        obj = obj.func
    return inspect.iscoroutine(obj)

class TaskManager(object):
    _managers = {}

    @classmethod
    def create(cls, name, **kwargs):
        if name in cls._managers:
            raise ValueError('named {} taskmanager already inited.'.format(name))
        inst = cls(name, **kwargs)
        cls._managers[name] = inst
        return inst

    @classmethod
    def get(cls, name="default"):
        if name not in cls._managers:
            raise ValueError('no named {} taskmanager. please init it before get it.'.format(name))
        return cls._managers.get(name)


    def __init__(self, name, **kwargs):
        self.pool_size = kwargs.get('pool_size') or 10
        self.name = name
        self.pool = AsyncPool(size=self.pool_size)

    async def spawn(self, coro):
        if not iscoroutine_or_partial(coro):
            raise Exception('Only coroutine supported.')
        try:
            await self.pool.spawn(coro)
        except CancelledError:
            return

    async def join(self, timeout=3):
        await self.pool.join(timeout)