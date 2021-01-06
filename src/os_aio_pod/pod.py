import asyncio
import logging
import time
from collections import OrderedDict
from functools import partial
from inspect import isclass, iscoroutine, iscoroutinefunction

from asyncio_dispatch import Signal

from os_aio_pod.bean import Bean, BeanContext


def create(config, *initializers):
    pod = None
    for i in initializers:
        p = i.init(config, pod)
        pod = p if p else pod
    return pod


class Pod(object):
    def __init__(self, config=None, loop=None):
        self._loop = loop if loop else asyncio.get_event_loop()
        self._beans = OrderedDict()
        self._label_index = {}
        self._finished = set()
        self._pending = set()
        self._coros = []
        self._bean_done_events = {}
        self._signal_dispatcher = Signal(loop=self._loop)
        self._stopped = self._started = False
        self._finished_event = asyncio.Event(loop=self._loop)
        self._stopping_event = asyncio.Event(loop=self._loop)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config

    @property
    def config(self):
        return self._config

    @property
    def loop(self):
        return self._loop

    async def wait_beans_done(self, bid_or_label):
        beans = self.get_beans(bid_or_label)
        await asyncio.wait(beans, loop=self._loop)

    def __ensure_status(self, status, true_or_false=True):
        s = "_" + status
        assert (
            hasattr(self, s) and getattr(self, s) == true_or_false
        ), f"Invalid status {status}: {true_or_false}"

    def add_bean(self, obj, label=None, **kwargs):
        self.__ensure_status("stopped", False)
        self.__ensure_status("started", False)
        self._preprocess(obj, label, **kwargs)

    def _load_beans(self):
        for obj, label, kwargs in self._coros:
            self._load_bean(obj, label, **kwargs)

    def _load_bean(self, obj, label=None, **kwargs):
        self._loop.set_task_factory(self._create_bean)
        try:
            bean = self._loop.create_task((obj, label, kwargs))
            self._beans[bean.id] = bean
            self._pending.add(bean.id)
            self._bean_done_events[bean.id] = asyncio.Event(loop=self._loop)
            bean.add_done_callback(partial(self._on_bean_done, bean.id))
            if bean.label:
                if bean.label not in self._label_index:
                    self._label_index[bean.label] = []
                self._label_index[bean.label].append(bean.id)
        finally:
            self._loop.set_task_factory(None)

    def get_beans(self, bid_or_label):
        bids = [bid_or_label]
        if isinstance(bid_or_label, str):
            bids = self._label_index[bid_or_label]
        return [self._beans[bid] for bid in bids]

    def _on_bean_done(self, bid, future):
        self._logger.debug(f"Bean finished {self._beans[bid]}")
        if bid in self._pending:
            self._pending.remove(bid)
        self._finished.add(bid)
        self._bean_done_events[bid].set()

    def _preprocess(self, obj, label=None, **kwargs):
        if not (
            iscoroutine(obj)
            or iscoroutinefunction(obj)
            or (
                isclass(obj)
                and hasattr(obj, "__call__")
                and iscoroutinefunction(obj.__call__)
            )
            or hasattr(obj, "__bean_label")
        ):
            raise TypeError(f"Invalid type {obj}")
        self._coros.append((obj, label, kwargs))

    def _create_bean(self, loop, kw):
        obj, label, kwargs = kw
        instance = None
        coro = obj
        idx = 1 if not self._beans else list(self._beans.keys())[-1] + 1
        pass_context = False
        if hasattr(obj, "__bean_label"):
            lb = getattr(obj, "__bean_label")
            if lb and not label:
                label = lb
            pass_context = True
        context = BeanContext(self, idx, label)

        if iscoroutine(obj):
            pass
        elif iscoroutinefunction(obj):
            coro = obj(**kwargs)
        elif (
            isclass(obj)
            and hasattr(obj, "__call__")
            and iscoroutinefunction(obj.__call__)
        ):
            instance = obj(context)
            coro = instance(**kwargs)
        elif pass_context:
            coro = obj(context, **kwargs)
        else:
            raise TypeError(f"Invalid type {obj}")

        context.instance = instance
        return Bean(context, coro, loop=self._loop)

    async def __signal(self, method, sig, callers=None, **kwargs):
        call = getattr(self._signal_dispatcher, method)
        return await call(key=sig, senders=callers, **kwargs)

    async def add_signal_handler(self, sig, callback, callers=None):
        return await self.__signal("connect", sig, callback=callback, callers=callers)

    async def remove_signal_handler(self, sig, callback, callers=None):
        return await self.__signal(
            "disconnect", sig, callback=callback, callers=callers
        )

    async def send_signal(self, sig, callers=None, **kwargs):
        return await self.__signal("send", sig, callers=callers, **kwargs)

    def stop(self, timeout=None, sig=None):
        self.__ensure_status("stopped", False)
        self.__ensure_status("started")
        if self._stopping_event.is_set():
            return
        asyncio.run_coroutine_threadsafe(
            self._stop(time.time(), timeout, sig), self._loop
        )

    async def _stop(self, event_time, timeout=None, sig=None):
        self._logger.debug(f"Stopping timeout: {timeout}")
        if sig:
            self._logger.debug(f"Recv signal {sig}")
            r = await self.send_signal(sig)
            self._logger.debug(f"Dispatch signal {sig} {r}")
        wait_time = timeout if timeout is None else event_time + timeout - time.time()
        try:
            await asyncio.wait_for(self._finished_event.wait(), timeout=wait_time)
        except:
            pass

        if self._pending:
            self._logger.debug(f"Stop pending beans")
        for bid in self._pending:
            self._beans[bid].cancel()
            self._logger.debug(f"Cancel bean {self._beans[bid]}")
        self._stopping_event.set()

    async def run(self):
        self.__ensure_status("stopped", False)
        self.__ensure_status("started", False)
        self._started = True

        self._logger.debug(f"Pod start")

        self._load_beans()

        for bean in self._beans.values():
            self._logger.debug(f"Pending bean: {bean}")

        # TODO
        # not a proper way to wait beans complete
        # when bean catch the CancelledError
        for next_complete in asyncio.as_completed(self._beans.values()):
            try:
                await next_complete
            except:
                pass

        self._finished_event.set()
        if not self._stopping_event.is_set():
            self.stop()
            await self._stopping_event.wait()
        self._started = False
        self._stopped = True
        self._logger.debug(f"Pod finished")
