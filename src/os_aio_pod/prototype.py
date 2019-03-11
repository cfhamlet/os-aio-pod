from typing import List, Union

from pydantic import BaseModel, validator

from os_aio_pod.utils import valid_log_level


class BeanConfig(BaseModel):

    label: str = None
    core: str

    class Config:
        allow_extra = True


class PodConfig(BaseModel):

    BEANS: List[dict] = []
    LOG_LEVEL: str = 'INFO'
    LOOP_TYPE: str = 'AUTO'
    DEBUG: bool = False

    @validator('LOG_LEVEL')
    def valid_log_level(cls, v):
        return valid_log_level(v)

    class Config:
        allow_extra = True
