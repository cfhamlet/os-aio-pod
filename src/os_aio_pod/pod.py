import asyncio
import time
from collections import OrderedDict
from functools import partial
from inspect import isawaitable, iscoroutine, iscoroutinefunction, isclass

from asyncio_dispatch import Signal

from os_aio_pod.bean import Bean, BeanContext


class Pod(object):
    def __init__(self):
        self._beans = OrderedDict()
        self._label_index = {}
        self._finished = set()
        self._pending = set()
        self._signal_dispatcher = Signal()
        self._stopped = self._started = False
        self._finished_event = asyncio.Event()
        self._stopping_event = None

    def __ensure_status(self, status, true_or_false=True):
        s = '_' + status
        assert hasattr(self, s) and getattr(
            self, s) == true_or_false, f'Invalid status {status}: {true_or_false}'

    def add_bean(self, obj, label=None, **kwargs):
        self.__ensure_status('stopped', False)
        self.__ensure_status('started', False)
        loop = asyncio.get_event_loop()
        loop.set_task_factory(self._create_bean)
        try:
            bean = loop.create_task((obj, label, kwargs))
            self._beans[bean.id] = bean
            self._pending.add(bean.id)
            bean.add_done_callback(partial(self._on_bean_done, bean.id))
            if bean.label:
                if bean.label not in self._label_index:
                    self._label_index = []
                self._label_index[bean.label].appned(bean.id)
        finally:
            loop.set_task_factory(None)

    def _on_bean_done(self, bid, future):
        if bid in self._pending:
            self._pending.remove(bid)
        self._finished.add(bid)

    def _create_bean(self, loop, kw):
        obj, label, kwargs = kw
        instance = None
        coro = obj
        idx = 1 if not self._beans else list(self._beans.keys())[-1] + 1
        context = BeanContext(self, idx, label, **kwargs)

        if iscoroutine(obj):
            pass
        elif iscoroutinefunction(obj):
            coro = obj(**kwargs)
        elif isclass(obj) and hasattr(obj, '__call__') and iscoroutinefunction(obj.__call__):
            instance = obj(context)
            coro = instance()
        else:
            raise TypeError(f'Invalid type {type(obj)}')

        context.instance = instance
        return Bean(context, coro)

    async def __signal(self, method, sig, callers=None, **kwargs):
        call = getattr(self._signal_dispatcher, method)
        return await call(key=sig, senders=callers, **kwargs)

    async def add_signal_handler(self, sig, callback, callers=None):
        return await self.__signal('connect', sig, callback=callback, callers=callers)

    async def remove_signal_handler(self, sig, callback, callers=None):
        return await self.__signal('disconnect', sig, callback=callback, callers=callers)

    async def send_signal(self, sig, callers=None, **kwargs):
        return await self.__signal('send', sig, callers=callers, **kwargs)

    async def stop(self, timeout=None):
        self.__ensure_status('stopped', False)
        self.__ensure_status('started')
        if self._stopping_event:
            return
        self._stopping_event = asyncio.Event()
        await self._stop(time.time(), timeout)

    async def _stop(self, event_time, timeout=None):
        force_time = event_time + (timeout if timeout else -1)
        wait_time = time.time() - force_time
        try:
            await asyncio.wait_for(self._finished_event.wait(), timeout=wait_time)
        except:
            pass
        for bid in self._pending:
            self._beans[bid].cancel()
        self._stopping_event.set()

    async def run(self):
        self.__ensure_status('stopped', False)
        self.__ensure_status('started', False)
        self._started = True

        for next_complete in asyncio.as_completed(self._beans.values()):
            try:
                await next_complete
            except:
                # TODO
                pass

        self._finished_event.set()
        await self.stop()
        await self._stopping_event.wait()
        self._started = False
        self._stopped = True
