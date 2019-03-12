from typing import List, Union

from pydantic import BaseModel, validator

from enum import Enum
import logging


class StrEnum(str, Enum):
    """Enum where members are also (and must be) string"""


class BeanConfig(BaseModel):

    label: str = None
    core: str

    class Config:
        allow_extra = True


class LogLevel(StrEnum):
    critical = 'critical'
    error = 'error'
    warning = 'warning'
    info = 'info'
    debug = 'debug'


def loop_types():
    s = {'asyncio'}
    try:
        import uvloop
        s.add('uvloop')
        s.add('auto')
    except:
        pass

    return dict([(i, i) for i in s])


LoopType = StrEnum('LoopType', loop_types())


class PodConfig(BaseModel):

    BEANS: List[dict] = []
    LOG_LEVEL: LogLevel = LogLevel.info
    LOOP_TYPE: LoopType = list(LoopType)[0] if len(
        LoopType) == 1 else LoopType.auto
    DEBUG: bool = False
    STOP_WAIT_TIME: int = None

    class Config:
        allow_extra = True
