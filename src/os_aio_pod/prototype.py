from typing import List, Union

from pydantic import BaseModel


class BeanConfig(BaseModel):

    label: str = None
    core: str

    class Config:
        allow_extra = True


class PotConfig(BaseModel):

    PEAS: List[dict] = []
    LOG_LEVEL: str = 'INFO'
    LOOP_TYPE: str = 'AUTO'
    DEBUG: bool = False

    class Config:
        allow_extra = True
