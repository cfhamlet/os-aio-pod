import asyncio

from os_aio_pod.contrib.simple import Server as BaseServer


class Server(BaseServer):
    async def produce(self, **kwargs):
        pass

    async def consume(self, obj, **kwargs):
        pass

    async def run(self, **kwargs):
        await super(Server, self).run(**kwargs)
        d = {"stop": False}
        consumer_num = kwargs.get("consumer_num", 10)
        queue_size = kwargs.get("queue_size", 10)
        queue = asyncio.Queue(maxsize=queue_size)

        def _on_stop(**kw):
            d["stop"] = True

        for signal in ("SIGTERM", "SIGINT"):
            await self.context.add_signal_handler(signal, _on_stop)

        class Stop:
            pass

        async def _consume():
            while True:
                obj = await queue.get()
                if isinstance(obj, Stop):
                    break
                await self.consume(obj, **kwargs)

        async def _produce():
            async for obj in self.produce(**kwargs):
                await queue.put(obj)
                if d["stop"]:
                    break
            for _ in range(consumer_num):
                await queue.put(Stop())

        tasks = [_produce()] + [_consume() for _ in range(consumer_num)]

        await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
