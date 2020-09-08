from asyncio import Task
from itertools import chain


class BeanContext(object):
    def __init__(self, pod, id, label=None):
        self.id = id
        self.label = label
        self.pod = pod
        self.instance = None

    @property
    def config(self):
        return self.pod.config

    async def wait_beans_done(self, bid_or_label):
        await self.pod.wait_beans_done(bid_or_label)

    def get_beans(self, bid_or_label):
        return self.pod.get_beans(bid_or_label)

    @property
    def loop(self):
        return self.pod.loop

    @property
    def bean(self):
        return self.pod.get_beans(self.id)[0]

    async def add_signal_handler(self, sig, callback):
        return await self.pod.add_signal_handler(
            sig, callback=callback, callers={self.bean}
        )

    async def remove_signal_handler(self, sig, callback):
        return await self.pod.remove_signal_handler(
            sig, callback=callback, callers={self.bean}
        )

    async def send_signal(self, sig, labels=None, **kwargs):
        beans = None
        if labels is not None:
            beans = set(chain(*[self.pod.get_beans(label) for label in labels]))
        return await self.pod.send_signal(sig, callers=beans, **kwargs)


class Bean(Task):
    def __init__(self, context, coro, *, loop=None):
        super(Bean, self).__init__(coro, loop=loop)
        self.context = context

    def _repr_info(self):
        info = super(Bean, self)._repr_info()
        info.append(f"{self.id}-{self.label}")
        return info

    @property
    def id(self):
        return self.context.id

    @property
    def label(self):
        return self.context.label
