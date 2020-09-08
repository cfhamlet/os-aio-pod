import asyncio


class HelloWorld(object):
    def __init__(self, context):
        self.context = context

    async def __call__(self, **kwargs):
        print("hello world!")
        print("kwargs", kwargs)
        print("sleep 1s")
        await asyncio.sleep(1)
