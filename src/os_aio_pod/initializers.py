import abc
import sys
import logging


class Initializer(abc.ABC):

    @abc.abstractmethod
    def init(self, pod, config):
        pass


class InitLoop(Initializer):

    def init(self, config, pod):
        pass


class InitLog(Initializer):

    def init(self, config, pod):
        logging.basicConfig(
            level=config.LOG_LEVEL,
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
