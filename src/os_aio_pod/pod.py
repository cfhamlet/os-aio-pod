import asyncio
import logging
import sys
import time
from collections import OrderedDict
from functools import partial
from inspect import isawaitable, isclass, iscoroutine, iscoroutinefunction

from asyncio_dispatch import Signal

from os_aio_pod.bean import Bean, BeanContext


def create(config, *initializers):
    pod = None
    for i in initializers:
        p = i.init(config, pod)
        pod = p if p else pod
    return pod


class Pod(object):
    def __init__(self):
        self._beans = OrderedDict()
        self._label_index = {}
        self._finished = set()
        self._pending = set()
        self._signal_dispatcher = Signal()
        self._stopped = self._started = False
        self._finished_event = asyncio.Event()
        self._stopping_event = asyncio.Event()
        self._logger = logging.getLogger(self.__class__.__name__)

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
                    self._label_index[bean.label] = []
                self._label_index[bean.label].append(bean.id)
        finally:
            loop.set_task_factory(None)

    def get_bean(self, bid):
        return self._beans.get(bid, None)

    def get_beans_by_label(self, label):
        return [self._beans[bid] for bid in self._label_index.get(label, [])]

    def _on_bean_done(self, bid, future):
        self._logger.debug(f'bean finished {self._beans[bid]}')
        if bid in self._pending:
            self._pending.remove(bid)
        self._finished.add(bid)

    def _create_bean(self, loop, kw):
        obj, label, kwargs = kw
        instance = None
        coro = obj
        idx = 1 if not self._beans else list(self._beans.keys())[-1] + 1
        context = BeanContext(self, idx, label)

        if iscoroutine(obj):
            pass
        elif iscoroutinefunction(obj):
            coro = obj(**kwargs)
        elif isclass(obj) and hasattr(obj, '__call__') and iscoroutinefunction(obj.__call__):
            instance = obj(context)
            coro = instance(**kwargs)
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

    def stop(self, timeout=None, sig=None):
        self.__ensure_status('stopped', False)
        self.__ensure_status('started')
        if self._stopping_event.is_set():
            return
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(
            self._stop(time.time(), timeout, sig), loop)

    async def _stop(self, event_time, timeout=None, sig=None):
        self._logger.debug(f'stopping timeout: {timeout}')
        if sig:
            self._logger.debug(f'recv signal {sig}')
            r = await self.send_signal(sig)
            self._logger.debug(f'dispatch signal {sig} {r}')
        wait_time = timeout if timeout is None else event_time + timeout - time.time()
        try:
            await asyncio.wait_for(self._finished_event.wait(), timeout=wait_time)
        except:
            pass
        self._logger.debug(f'stopping pending beans')
        for bid in self._pending:
            self._beans[bid].cancel()
            self._logger.debug(f'cancel bean {self._beans[bid]}')
        self._stopping_event.set()

    async def run(self):
        self.__ensure_status('stopped', False)
        self.__ensure_status('started', False)
        self._started = True

        self._logger.debug(f'pod start')
        for bean in self._beans.values():
            self._logger.debug(f'panding bean: {bean}')

        for next_complete in asyncio.as_completed(self._beans.values()):
            try:
                await next_complete
            except:
                pass

        self._finished_event.set()
        self.stop()
        await self._stopping_event.wait()
        self._started = False
        self._stopped = True
        self._logger.debug(f'pod finished')
