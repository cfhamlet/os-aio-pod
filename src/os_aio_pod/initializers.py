import abc
import asyncio
import logging
import sys
from signal import Signals

from os_aio_pod.pod import Pod
from os_aio_pod.utils import load_obj, pydantic_items


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

        def setup_auto():
            try:
                setup_uvloop()
                return
            except:
                pass
            setup_asyncio()

        {"auto": setup_auto, "uvloop": setup_uvloop, "asyncio": setup_asyncio}.get(
            config.LOOP_TYPE.value
        )()

        loop = asyncio.get_event_loop()
        return Pod(config=config, loop=loop)


class InitLog(Initializer):
    def init(self, config, pod):
        logging.basicConfig(
            level=config.LOG_LEVEL.value.upper(),
            format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class InitDebug(Initializer):
    def init(self, config, pod):
        if config.DEBUG:
            pod.loop.set_debug(True)
            logging.getLogger().setLevel(logging.DEBUG)


class InitSignal(Initializer):
    def init(self, config, pod):
        for sig in (Signals.SIGINT, Signals.SIGTERM):
            pod.loop.add_signal_handler(
                sig.value, pod.stop, config.STOP_WAIT_TIME, sig.name
            )


class InitBeans(Initializer):
    def _load_bean(self, pod, bean_config):
        obj = load_obj(bean_config.core)
        kwargs = dict(pydantic_items(bean_config, exclude={"core"}))
        pod.add_bean(obj, **kwargs)

    def init(self, config, pod):
        sys.path.insert(0, ".")
        logger = logging.getLogger(self.__class__.__name__)
        for bean_config in config.BEANS:
            try:
                self._load_bean(pod, bean_config)
            except Exception as e:
                logger.error(f"Init bean error {e}")
