from enum import Enum
from typing import List

from pydantic import BaseSettings

ENV_PREFIX = "OS_AIO_POD_"


class StrEnum(str, Enum):
    """Enum where members are also (and must be) string"""


class BeanConfig(BaseSettings):

    label: str = None
    core: str

    class Config:
        env_prefix = ENV_PREFIX
        extra = "allow"


class LogLevel(StrEnum):
    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"


def loop_types():
    s = {"asyncio"}
    try:
        s.add("uvloop")
        s.add("auto")
    except:
        pass

    return dict([(i, i) for i in s])


LoopType = StrEnum("LoopType", loop_types())


class PodConfig(BaseSettings):

    BEANS: List[BeanConfig] = []
    LOG_LEVEL: LogLevel = LogLevel.info
    LOOP_TYPE: LoopType = list(LoopType)[0] if len(LoopType) == 1 else LoopType.auto
    DEBUG: bool = False
    STOP_WAIT_TIME: int = None

    class Config:
        env_prefix = ENV_PREFIX
        extra = "allow"
        validate_all = True


class BlankConfig(BaseSettings):
    class Config:
        env_prefix = ENV_PREFIX
        extra = "allow"
