import abc
import asyncio
import logging
import sys

from os_aio_pod.pod import Pod
from os_aio_pod.prototype import LoopType


class Initializer(abc.ABC):

    @abc.abstractmethod
    def init(self, config, pod):
        pass


class InitLoop(Initializer):

    def init(self, config, pod):
        assert pod is None

        def setup_uvloop():
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        def setup_asyncio():
            pass

        {
            'auto': setup_uvloop,
            'uvloop': setup_uvloop,
            'asyncio': setup_asyncio
        }.get(config.LOOP_TYPE.value)()

        return Pod()


class InitLog(Initializer):

    def init(self, config, pod):
        logging.basicConfig(
            level=config.LOG_LEVEL.value.upper(),
            format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )


class InitBeans(Initializer):

    def init(self, config, pod):
        pass


class InitDebug(Initializer):

    def init(self, config, pod):
        if config.DEBUG:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.set_debug(True)
            logging.getLogger().setLevel(logging.DEBUG)


class InitSignal(Initializer):

    def init(self, config, pod):
        pass
