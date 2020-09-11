import inspect


class Server(object):
    def __init__(self, context):
        self.context = context

    @property
    def config(self):
        self.context.config

    def on_stop(self, **kwargs):
        pass

    async def startup(self, **kwargs):
        pass

    async def cleanup(self, **kwargs):
        pass

    async def __call__(self, **kwargs):
        for signal in ("SIGTERM", "SIGINT"):
            await self.context.add_signal_handler(signal, self.on_stop)
            await self.context.add_signal_handler(signal, self.on_stop)

        d = self.startup(**kwargs)

        if inspect.isawaitable(d):
            await d

        await self.run(**kwargs)

        d = self.cleanup(**kwargs)
        if inspect.isawaitable(d):
            await d

    async def run(self, **kwargs):
        pass
